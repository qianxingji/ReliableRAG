"""Normalized-EM transitions and all fixed-membership subgroup reports."""
import math
from controls import require
from design import METHODS, VARIANTS, HELDOUT, RETRIEVERS

def metric(keys, selected, ys, cap=None):
    keys=set(keys); selected=keys & set(selected); ordered=sorted(selected)
    r=sum(ys[k]['a0_em']==0 and ys[k]['a1_em']==1 for k in selected)
    d=sum(ys[k]['a0_em']==1 and ys[k]['a1_em']==0 for k in selected)
    return dict(N_all=len(keys),actions=len(selected),recovery=r,damage=d,neutral=len(selected)-r-d,net=r-d,
        delta_em_pp=100*(r-d)/len(keys) if keys else None,
        delta_f1_pp=100*math.fsum(ys[k]['a1_f1']-ys[k]['a0_f1'] for k in ordered)/len(keys) if keys else None,
        cap=cap)
def summary(keys, selections, ys, cap=None):
    mm={m:metric(keys,selections[m],ys,cap) for m in METHODS}
    compare={v:{m:dict(delta_em_pp=mm[v]['delta_em_pp']-mm[m]['delta_em_pp'] if keys else None,
                       delta_f1_pp=mm[v]['delta_f1_pp']-mm[m]['delta_f1_pp'] if keys else None,
                       net_difference=mm[v]['net']-mm[m]['net'],damage_difference=mm[v]['damage']-mm[m]['damage'])
                for m in METHODS if m!=v} for v in VARIANTS}
    return dict(methods=mm,comparisons=compare)
def breakdown(keys, selections, ys):
    answer={}
    for kind in ('dataset','retriever','dataset_x_retriever'):
        cells=[]
        labels=sorted(HELDOUT) if kind=='dataset' else RETRIEVERS if kind=='retriever' else [(d,r) for d in sorted(HELDOUT) for r in RETRIEVERS]
        for label in labels:
            kk={k for k in keys if (k[0] if kind=='dataset' else k[1] if kind=='retriever' else (k[0],k[1]))==label}
            cells.append(dict(cell=label,summary=summary(kk,selections,ys)))
        answer[kind]=cells
    return answer
