/* Presentation only: package bytes, URLs and hashes come from the unchanged catalog. */
(() => {
  'use strict';
  const root = document.querySelector('[data-dataset-downloads]');
  if (!root) return;
  const zh = document.documentElement.lang.toLowerCase().startsWith('zh');
  const t = (en, cn) => zh ? cn : en;
  const number = value => Number(value).toLocaleString(zh ? 'zh-CN' : 'en-US');
  const validBytes = value => Number.isSafeInteger(value) && value >= 0;
  const size = value => validBytes(value) ? `${(value / 1e9).toLocaleString(zh ? 'zh-CN' : 'en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})} GB` : '—';
  const el = (tag, text, className) => {
    const node = document.createElement(tag);
    if (text != null) node.textContent = text;
    if (className) node.className = className;
    return node;
  };
  const icon = () => {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '1.6');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    const path = document.createElementNS(svg.namespaceURI, 'path');
    path.setAttribute('d', 'M12 3v12m-4-4 4 4 4-4M5 16v4h14v-4');
    svg.append(path);
    return svg;
  };
  const expected = ['mars-baseline', 'mars-second', 'moon-baseline', 'moon-second', 'cabin-baseline', 'cabin-second'];
  const frameCounts = {mars: 9879, moon: 10821, cabin: 12100};
  const names = {mars: t('Mars', '火星'), moon: t('Moon', '月球'), cabin: t('Cabin', '太空舱')};
  const conditions = {
    'mars-baseline': t('Solar elevation 35°', '太阳高度角 35°'),
    'mars-second': t('Solar elevation 8°', '太阳高度角 8°'),
    'moon-baseline': 'A/B: sunlit · C: psr',
    'moon-second': 'A/B: sun_east · C: sunlit',
    'cabin-baseline': t('Normal light', '正常光照'),
    'cabin-second': t('Dim light', '暗光')
  };
  const status = root.querySelector('[data-download-status]');
  const catalog = root.querySelector('[data-download-cards]');
  const metadata = root.querySelector('[data-download-metadata]');
  const stats = root.querySelector('[data-download-stats]');
  const data = window.SPACE_VLA_DOWNLOADS;
  if (!data || data.schema_version !== 1 || !Array.isArray(data.groups)) {
    status.textContent = t('The download catalog is currently unavailable.', '下载清单暂不可用。');
    return;
  }
  const groups = expected.map(id => data.groups.find(group => group.id === id));
  const complete = groups.every((g, i) => g && g.routes === 300 && g.frames === frameCounts[expected[i].split('-')[0]] && Array.isArray(g.archives) && g.archives.length > 0 && g.archives.every(f => f && typeof f.filename === 'string' && validBytes(f.bytes) && /^[a-fA-F0-9]{64}$/.test(f.sha256 || '')));
  if (!complete) {
    status.textContent = t('The dataset packages are being prepared.', '数据包正在准备中。');
    return;
  }
  let localAvailable = false;
  let openedId = null;
  const publicUrl = value => {
    if (typeof value !== 'string' || !value) return null;
    try {
      const url = new URL(value);
      return url.protocol === 'https:' && !url.username && !url.password ? url.href : null;
    } catch (_) { return null; }
  };
  const resolvedUrl = file => {
    if (publicUrl(file.url)) return publicUrl(file.url);
    return localAvailable && data.status === 'local_ready' && typeof file.local_url === 'string' && /^\/dataset-downloads\/[A-Za-z0-9][A-Za-z0-9_.-]*$/.test(file.local_url) ? file.local_url : null;
  };
  const fileLink = (file, label, className) => {
    const url = file && resolvedUrl(file);
    const link = el(url ? 'a' : 'span', null, className + (url ? '' : ' is-disabled'));
    link.append(icon(), el('span', label));
    if (url) {
      link.href = url;
      link.download = file.filename;
    } else {
      link.setAttribute('aria-disabled', 'true');
      link.title = t('Online download is not published. Use the local preview for prepared files.', '线上下载尚未发布，可通过本地预览下载已准备的文件。');
    }
    return link;
  };
  const render = () => {
    const allFiles = groups.flatMap(group => group.archives);
    const allPublic = allFiles.every(file => publicUrl(file.url));
    status.dataset.state = allPublic || localAvailable ? 'ready' : 'pending';
    status.textContent = allPublic ? t('Downloads available', '可下载') : localAvailable ? t('Local downloads available · online release pending', '本地可下载 · 线上尚未发布') : t('Online release pending · prepared files are available through the local preview', '线上尚未发布 · 已准备的数据包可通过本地预览下载');
    stats.replaceChildren(el('strong', size(allFiles.reduce((sum, file) => sum + file.bytes, 0))), el('span', t(`Full dataset · 6 groups · ${allFiles.length} ZIP files`, `完整数据集 · 6 组 · ${allFiles.length} 个 ZIP`)));
    metadata.replaceChildren(fileLink(data.manifest, t('Manifest', '数据清单'), 'download-resource'), fileLink(data.checksums, 'SHA256', 'download-resource'));
    catalog.replaceChildren();
    const table = el('table', null, 'download-table');
    table.setAttribute('aria-label', t('Dataset downloads by world and lighting', '按世界与光照下载数据'));
    const thead = el('thead');
    const header = el('tr');
    [t('World', '世界'), t('Lighting', '光照'), t('Routes', '路线'), t('Frames', '帧数'), t('Size', '体积'), t('Download', '下载')].forEach((label, i) => {
      const th = el('th', label, i >= 2 && i <= 4 ? 'download-number' : i === 5 ? 'download-action' : '');
      th.scope = 'col';
      header.append(th);
    });
    thead.append(header);
    table.append(thead);
    const toggles = [];
    groups.forEach(group => {
      const world = group.id.split('-')[0];
      const light = group.id.endsWith('-second') ? t('Second lighting', '第二光照') : t('Baseline', '基准光照');
      const body = el('tbody');
      const row = el('tr', null, 'download-row');
      const worldCell = el('th', null, 'download-world');
      worldCell.scope = 'row';
      const worldLabel = el('span', null, 'download-world-label');
      const dot = el('span', null, 'download-world-dot');
      dot.dataset.world = world;
      dot.setAttribute('aria-hidden', 'true');
      worldLabel.append(dot, el('span', names[world]));
      worldCell.append(worldLabel);
      const lightCell = el('td', null, 'download-light');
      lightCell.append(el('strong', light), el('span', conditions[group.id], 'download-condition'));
      const routeCell = el('td', number(group.routes), 'download-number');
      routeCell.title = '60 dev + 240 test';
      const sizeCell = el('td', size(group.archives.reduce((sum, file) => sum + file.bytes, 0)), 'download-number');
      sizeCell.title = `${number(group.archives.reduce((sum, file) => sum + file.bytes, 0))} ${t('bytes', '字节')}`;
      const actionCell = el('td', null, 'download-action');
      const button = el('button', null, 'download-toggle');
      button.type = 'button';
      button.setAttribute('aria-label', t(`Show ${group.archives.length} ZIP downloads for ${names[world]}, ${light}`, `展开${names[world]}${light}的 ${group.archives.length} 个 ZIP`));
      button.setAttribute('aria-controls', `download-files-${group.id}`);
      button.append(el('span', `${group.archives.length} ZIPs`), el('span', null, 'download-chevron'));
      actionCell.append(button);
      row.append(worldCell, lightCell, routeCell, el('td', number(group.frames), 'download-number'), sizeCell, actionCell);
      const detailRow = el('tr', null, 'download-detail-row');
      detailRow.id = `download-files-${group.id}`;
      const detailCell = el('td');
      detailCell.colSpan = 6;
      const panel = el('div', null, 'download-detail');
      const heading = el('div', null, 'download-detail-heading');
      heading.append(el('strong', `${names[world]} · ${light}`), el('span', t('Download every part in this group.', '请下载此组的全部分包。')));
      const list = el('ul', null, 'download-parts');
      group.archives.forEach((file, i) => {
        const item = el('li');
        const part = el('div');
        part.title = file.filename;
        part.append(el('span', t(`Part ${String(i + 1).padStart(2, '0')}`, `分包 ${String(i + 1).padStart(2, '0')}`), 'download-part-label'), el('span', size(file.bytes), 'download-part-size'));
        const download = fileLink(file, t('Download', '下载'), 'download-file-link');
        download.setAttribute('aria-label', t(`Download ${file.filename}`, `下载 ${file.filename}`));
        item.append(part, download);
        list.append(item);
      });
      const checks = el('details', null, 'download-checksums');
      checks.append(el('summary', t('Filenames & SHA256 checksums', '查看完整文件名与 SHA256')));
      const checkList = el('ul');
      group.archives.forEach(file => {
        const item = el('li');
        item.append(el('span', `${file.filename} · ${number(file.bytes)} ${t('bytes', '字节')}`, 'download-filename'), el('code', file.sha256));
        checkList.append(item);
      });
      checks.append(checkList);
      panel.append(heading, list, checks);
      detailCell.append(panel);
      detailRow.append(detailCell);
      const setOpen = open => {
        button.setAttribute('aria-expanded', String(open));
        row.classList.toggle('is-open', open);
        detailRow.hidden = !open;
      };
      setOpen(openedId === group.id);
      toggles.push({id: group.id, setOpen});
      button.addEventListener('click', () => {
        openedId = openedId === group.id ? null : group.id;
        toggles.forEach(toggle => toggle.setOpen(toggle.id === openedId));
      });
      body.append(row, detailRow);
      table.append(body);
    });
    catalog.append(table);
  };
  render();
  if (['localhost', '127.0.0.1'].includes(location.hostname) && ['http:', 'https:'].includes(location.protocol) && data.status === 'local_ready') {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);
    fetch('/dataset-downloads/status.json', {signal: controller.signal, cache: 'no-store', credentials: 'omit'})
      .then(response => response.ok ? response.json() : null)
      .then(result => { if (result && result.available === true) { localAvailable = true; render(); } })
      .catch(() => {})
      .finally(() => clearTimeout(timeout));
  }
})();
