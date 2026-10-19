"""Immutable daily PDF snapshots. Standard library only; no deletion policy.
One first successful PDF per Europe/Berlin date. Persist report-archive/ in git.
Latest may update intraday; dated snapshots never overwrite an existing valid PDF.
"""
from pathlib import Path
import datetime
import html
import os
import shutil
from zoneinfo import ZoneInfo
MAX_PDF_BYTES = 5 * 1024 * 1024

def valid_pdf(path):
    p=Path(path)
    if not p.is_file() or not 1000 <= p.stat().st_size <= MAX_PDF_BYTES:return False
    with p.open('rb') as f:
        if f.read(5)!=b'%PDF-':return False
        f.seek(max(0,p.stat().st_size-2048))
        return b'%%EOF' in f.read()

def atomic_copy(source, target):
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_name(target.name+'.tmp')
    shutil.copyfile(source,tmp);os.replace(tmp,target)

def sync(root, output, current, prefix, now=None, seed_only=False, archive_today=True):
    root=Path(root);output=Path(output);output.mkdir(parents=True,exist_ok=True)
    store=root/'report-archive';store.mkdir(exist_ok=True)
    now=now or datetime.datetime.now(ZoneInfo('Europe/Berlin'))
    if now.tzinfo is None:raise ValueError('Archive timestamp must include timezone')
    day=now.astimezone(ZoneInfo('Europe/Berlin')).date().isoformat()
    snapshot=store/(day+'.pdf');latest=output/current
    # Existing dated PDFs can seed the archive, without inventing past reports.
    for p in sorted(output.glob(prefix+'????-??-??.pdf')):
        date=p.name[len(prefix):-4]
        try:datetime.date.fromisoformat(date)
        except ValueError:continue
        target=store/(date+'.pdf')
        if valid_pdf(p) and not valid_pdf(target):atomic_copy(p,target)
    if archive_today and not seed_only and valid_pdf(latest) and not valid_pdf(snapshot):atomic_copy(latest,snapshot)
    dates=[]
    for p in sorted(store.glob('????-??-??.pdf'),reverse=True):
        try:datetime.date.fromisoformat(p.stem)
        except ValueError:continue
        if valid_pdf(p):
            dates.append(p.stem);atomic_copy(p,output/(prefix+p.name))
    if not seed_only and not valid_pdf(latest) and dates:
        atomic_copy(store/(dates[0]+'.pdf'),latest)
        print('::warning::PDF generation failed or unavailable; keeping last valid archived report from '+dates[0])
    return dates

def archive_html(dates, prefix):
    links=''.join('<li><a href="/berichte/%s%s.pdf">%s · PDF</a></li>'%(html.escape(prefix),d,d) for d in dates)
    return '<section class="report-archive"><h2>Tagesarchiv</h2><p>Eine feste Ausgabe pro Berliner Kalendertag: der erste erfolgreiche Lauf. Aktuelle Ausgabe kann später am Tag aktualisiert werden. Bei Fehlern bleibt die letzte gültige Ausgabe erhalten.</p><ul>'+ (links or '<li>Noch keine archivierte Ausgabe verfügbar.</li>')+'</ul></section>'
