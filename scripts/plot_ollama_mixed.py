"""Export an engineering figure from the offline audit; requires matplotlib."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def main():
    p = argparse.ArgumentParser()
    p.add_argument('report'); p.add_argument('output_prefix')
    args = p.parse_args()
    rows = json.loads(Path(args.report).read_text())['main']['turns']
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(3, 1, figsize=(11.4, 8.5), sharex=True,
                             gridspec_kw={'height_ratios': [1.3, 1, 1]})
    fig.subplots_adjust(left=.095, right=.965, top=.84, bottom=.14, hspace=.31)
    fig.suptitle('Qwen / Gemma: mixed-model engineering qualification',
                 x=.095, y=.97, ha='left', fontsize=17, weight='bold')
    fig.text(.095, .925, '50 messages · thinking off · 512-token output allowance · one RF trajectory', fontsize=11)
    colors = {'A': '#176c98', 'B': '#c96328'}
    fields = ['input_tokens', 'visible_words', 'http_seconds']
    labels = ['Recipient input tokens', 'Visible words', 'Generation HTTP time (s)']
    for ax, field, label in zip(axes, fields, labels):
        ax.axvspan(30.5, 40.5, color='#e4dcf0', alpha=.65, zorder=0)
        ax.axvline(30.5, color='#85718c', linestyle=':', lw=1)
        ax.axvline(40.5, color='#85718c', linestyle=':', lw=1)
        ax.plot([r['turn'] for r in rows], [r[field] for r in rows], color='#aeb8c0', lw=1, zorder=1)
        for model in ('A', 'B'):
            group = [r for r in rows if r['model'] == model]
            ax.scatter([r['turn'] for r in group], [r[field] for r in group], s=24,
                       color=colors[model], marker='o' if model == 'A' else 's', zorder=3)
        ax.set_ylabel(label); ax.grid(axis='y', color='#e4e8eb', lw=.7)
        ax.set_xlim(.5, 50.5); ax.set_ylim(bottom=0)
    axes[0].text(15.5, 1.035, 'Full history', transform=axes[0].get_xaxis_transform(), ha='center')
    axes[0].text(35.5, 1.035, 'Recent three', transform=axes[0].get_xaxis_transform(), ha='center')
    axes[0].text(45.5, 1.035, 'Full restored', transform=axes[0].get_xaxis_transform(), ha='center')
    axes[1].axhline(150, color='#9d2b48', linestyle='--', lw=1)
    axes[1].text(1.5, 153, 'Requested word limit', color='#9d2b48', fontsize=9)
    axes[-1].set_xlabel('Generated message number')
    axes[-1].set_xticks([1, 10, 20, 30, 40, 50])
    fig.legend(handles=[Line2D([], [], color=colors[m], marker=marker, ls='', label=label)
                        for m, marker, label in [('A', 'o', 'A / Qwen 30B'), ('B', 's', 'B / Gemma 26B')]],
               loc='upper right', bbox_to_anchor=(.967, .90), frameon=False, ncol=2)
    fig.text(.095, .032, 'Task-directed engineering data. Token counts agree with recipient preflight; generation input IDs are not captured.\n'
             'HTTP timing excludes inter-request checks and the planned restart. Native caching remained enabled.', fontsize=9, color='#4d5862')
    output = Path(args.output_prefix); output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(output)+'.png', dpi=170, facecolor='white')
    svg = Path(str(output)+'.svg')
    fig.savefig(svg, facecolor='white')
    # Matplotlib SVG includes whitespace-only lines; normalize before hashing.
    svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
    plt.close(fig)


if __name__ == '__main__':
    main()
