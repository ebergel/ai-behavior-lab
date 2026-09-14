"""Create an exportable engineering figure with optional matplotlib.

The plotting dependency is separate from the standard-library instrument core.
"""
import argparse
import json
import os
from pathlib import Path
import tempfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument('report')
    p.add_argument('output_stem')
    args = p.parse_args()
    report = json.loads(Path(args.report).read_text())
    rows = report['main']['turns']
    stem = Path(args.output_stem)
    outputs = [stem.with_suffix(ext) for ext in ('.png', '.svg')]
    if any(path.exists() for path in outputs):
        raise ValueError('Use a new figure filename; existing evidence is not overwritten')
    stem.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'behaviorlab-matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import StrMethodFormatter
    x = [r['turn'] for r in rows]
    reasoning = [r['reasoning_tokens'] or 0 for r in rows]
    other = [r['completion_tokens'] - n for r, n in zip(rows, reasoning)]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'axes.labelcolor': '#263346', 'text.color': '#263346',
                         'xtick.color': '#526173', 'ytick.color': '#526173'})
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.2), sharex=True, gridspec_kw={'hspace': .25})
    fig.subplots_adjust(top=.84, bottom=.13, left=.13, right=.97)
    fig.suptitle('MTPLX: 50-turn technical trajectory', x=.13, y=.97, ha='left', fontsize=19, fontweight='bold')
    fig.text(.13, .927, 'One RF trajectory • reasoning on/medium • session-cache bypass', fontsize=11)
    for ax in axes:
        ax.axvspan(30.5, 40.5, color='#eaf2f8', zorder=0)
        for boundary in (30.5, 40.5):
            ax.axvline(boundary, color='#94a8b9', linewidth=.8, linestyle=':')
        ax.grid(axis='y', color='#dbe1e7', linewidth=.6, zorder=0)
        ax.set_xlim(.5, 50.5)
        ax.yaxis.set_major_formatter(StrMethodFormatter('{x:,.0f}'))
    for at, label in ((15.5, 'Full history'), (35.5, 'Recent three'), (45.5, 'Restored full')):
        axes[0].text(at, 1.06, label, transform=axes[0].get_xaxis_transform(), ha='center', fontsize=10)
    axes[0].plot(x, [r['prompt_tokens'] for r in rows], '-o', color='#216b9d', linewidth=1.5, markersize=3)
    axes[0].set_ylabel('Rendered input\n(tokens)')
    axes[0].set_ylim(bottom=0)
    axes[1].bar(x, reasoning, color='#b7762d', width=.74, label='Reasoning', zorder=2)
    axes[1].bar(x, other, bottom=reasoning, color='#86a8c4', width=.74, label='Other generated tokens', zorder=2)
    caps = [r['output_reserve'] for r in rows]
    axes[1].plot(x, caps, '--', color='#475569', linewidth=1, label='Output allowance')
    axes[1].set_ylabel('Generated output\n(tokens)')
    axes[1].legend(loc='upper left', fontsize=8, frameon=False, ncol=3)
    axes[1].set_ylim(0, max(caps) * 1.2)
    axes[2].plot(x, [r['http_seconds'] for r in rows], '-o', color='#287c67', linewidth=1.2, markersize=3)
    axes[2].set_ylabel('Generation HTTP\ntime (seconds)')
    axes[2].set_ylim(bottom=0)
    axes[2].set_xticks([1, 10, 20, 30, 40, 50])
    axes[2].set_xlabel('Generated participant message')
    fig.text(.13, .035, 'Engineering stimulus; not a behavioral experiment. Timings exclude artifact verification and tokenizer preflight.\n'
             'Earlier output-cap failures are retained separately. This figure shows only the selected completed trajectory.',
             fontsize=8.5, color='#526173')
    for path in outputs:
        fig.savefig(path, dpi=180, facecolor='white', metadata={'Creator': 'Behavior Laboratory / matplotlib'})
    plt.close(fig)
    print(json.dumps({'files': [str(p.resolve()) for p in outputs], 'matplotlib_version': matplotlib.__version__}))


if __name__ == '__main__':
    main()
