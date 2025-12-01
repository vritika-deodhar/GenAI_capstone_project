from typing import List, Dict
def aggregate_summaries(summaries: List[Dict]) -> Dict:
    themes = []
    methods = {}
    for s in summaries:
        pr = s.get('problem','')
        if pr and pr not in themes:
            themes.append(pr)
        for m in s.get('methods',[]):
            methods.setdefault(m,0); methods[m]+=1
    return {'num_papers': len(summaries), 'themes': themes, 'method_counts': methods}
