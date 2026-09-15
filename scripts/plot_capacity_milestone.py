"""Optional scientific figure from the saved capacity audit."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('audit'); p.add_argument('output'); args=p.parse_args()
    report=json.loads(Path(args.audit).read_text())
    fig,axes=plt.subplots(2,2,figsize=(10.5,6.7),sharex=True,sharey=True)
    for ax,job,title,color in zip(axes.flat,['long-AA-1','long-AA-2','long-BB-1','long-BB-2'],
                                ['Qwen · root 1','Qwen · root 2','Gemma · root 1','Gemma · root 2'],
                                ['#245976','#245976','#9B5C32','#9B5C32']):
        rows=[r for r in report['calls'] if r['job']==job]
        ax.plot([r['turn'] for r in rows],[r['visible_words'] for r in rows],color=color,lw=1.7)
        capped=[r for r in rows if r['finish_reason']=='length']
        if capped:
            ax.scatter([r['turn'] for r in capped],[r['visible_words'] for r in capped],c='#BE283D',marker='x',s=70,lw=2,zorder=4)
            first=capped[0]
            label=f"{first['generated_tokens']:,}-token cap\n{first['most_frequent_line_count']} identical lines"
            ax.annotate(label,xy=(first['turn'],first['visible_words']),xytext=(5,730),fontsize=8,
                        arrowprops={'arrowstyle':'->','color':'#BE283D'},color='#9C2030')
            ax.axvspan(first['turn']+.5,50.5,color='#EEEEEE',zorder=0)
        ax.axhline(150,ls='--',c='#777777',lw=.8)
        ax.set_title(title,loc='left',fontsize=11); ax.set_xlim(.5,50.5)
        ax.set_ylim(0,1000); ax.grid(axis='y',alpha=.16); ax.spines[['top','right']].set_visible(False)
    for ax in axes[-1]:ax.set_xlabel('Participant message number')
    for ax in axes[:,0]:ax.set_ylabel('Visible words (whitespace count)')
    fig.suptitle('Larger output allowance: three complete roots, one repetition failure',x=.075,ha='left',fontsize=13)
    fig.text(.075,.035,'All fresh roots: 32,768-token context, 2,048-token output allowance, thinking off. Dashed line: soft 150-word instruction.',fontsize=8)
    fig.text(.075,.014,'Red cross: capped reply, preserved. Gray: 21 blocked descendants. Engineering capacity trial; no semantic qualification claim.',fontsize=8)
    fig.tight_layout(rect=(0,.07,1,.945))
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(path.with_suffix('.png'),dpi=180);fig.savefig(path.with_suffix('.svg'))
    svg=path.with_suffix('.svg');svg.write_text('\n'.join(line.rstrip() for line in svg.read_text().splitlines())+'\n')
