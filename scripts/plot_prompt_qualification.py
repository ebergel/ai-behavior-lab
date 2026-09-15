"""Optional scientific figure from audited calls; matplotlib is not a core dependency."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def main():
    p = argparse.ArgumentParser(); p.add_argument('directory'); p.add_argument('output'); args = p.parse_args()
    base = Path(args.directory); output = Path(args.output)
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.5), sharex=True, sharey=True)
    colors = ['#176B8B', '#A45136']
    maximum_words = 150
    panels = [('qwen-reference', 'AA', 'Qwen reference · 400 tokens · thinking off'),
              ('gemma-reference', 'BB', 'Gemma reference · 2,500 tokens · thinking on'),
              ('common', 'AA', 'Common Qwen · 512 tokens · thinking off'),
              ('common', 'BB', 'Common Gemma · 512 tokens · thinking off')]
    for ax, (job, pairing, title) in zip(axes.flat, panels):
        rows = json.loads((base/job/'call-audit.json').read_text())['calls']
        for i, color in enumerate(colors, 1):
            selected = [r for r in rows if r['node'].startswith(pairing+'-'+str(i)+':')]
            maximum_words = max(maximum_words, *(r['visible_words'] for r in selected))
            ax.plot([int(r['node'].rsplit(':', 1)[1]) for r in selected],
                    [r['visible_words'] for r in selected], color=color, linewidth=1.6)
            capped = [r for r in selected if r['finish_reason'] == 'length']
            ax.scatter([int(r['node'].rsplit(':', 1)[1]) for r in capped], [r['visible_words'] for r in capped],
                       marker='x', s=65, linewidths=2, color='#B42336', zorder=4)
        ax.axhline(150, color='#666666', linestyle='--', linewidth=.8)
        ax.axvspan(24.5, 30.5, color='#E3E7EB', alpha=.65, zorder=0)
        ax.set_title(title, fontsize=10, loc='left'); ax.set_xlim(.5, 30.5); ax.set_ylim(bottom=0)
        ax.grid(axis='y', alpha=.15); ax.spines[['top', 'right']].set_visible(False)
    for ax in axes.flat: ax.set_ylim(0, maximum_words*1.08)
    for ax in axes[-1]: ax.set_xlabel('Participant message number')
    for ax in axes[:, 0]: ax.set_ylabel('Visible words (whitespace count)')
    fig.suptitle('Qualification: reply length and output caps', x=.07, ha='left', fontsize=15)
    fig.legend([Line2D([0],[0],color=colors[0]), Line2D([0],[0],color=colors[1]),
                Line2D([0],[0],marker='x',color='#B42336',linestyle='None')],
               ['Root 1', 'Root 2', 'Output cap'], loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.5,.045))
    fig.text(.07,.025,'Gray band: fixed review window 25–30. Dashed line: soft 150-word instruction. Traces excluded from word counts.', fontsize=8)
    fig.tight_layout(rect=(0,.10,1,.94))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output.with_suffix('.png'), dpi=180)
    fig.savefig(output.with_suffix('.svg'))
    svg = output.with_suffix('.svg')
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


if __name__ == '__main__': main()
