import {build} from 'esbuild';
import {readFile,writeFile} from 'node:fs/promises';
await build({entryPoints:['web/analysis/main.jsx'],bundle:true,minify:true,format:'iife',globalName:'LabAnalysis',outfile:'behaviorlab/explorer_ui/analysis-widget.js',define:{'process.env.NODE_ENV':'"production"'},legalComments:'eof'});
const lock=JSON.parse(await readFile('web/analysis/package-lock.json'));
const packages=Object.entries(lock.packages).filter(([name,p])=>name&&!p.dev).map(([name])=>name.replace(/^node_modules\//,''));
let notices='Analysis workspace bundled dependency notices\nBuild dependencies and exact versions: web/analysis/package-lock.json\n\n';
for(const pkg of packages){const dir=`web/analysis/node_modules/${pkg}`;try{const p=JSON.parse(await readFile(`${dir}/package.json`));let license='';for(const f of ['LICENSE','LICENSE.txt','LICENSE.md','LICENSE-MIT']){try{license=await readFile(`${dir}/${f}`,'utf8');break;}catch{}}notices+=`\n${pkg} ${p.version} (${p.license})\n${license}\n`;}catch{}}
await writeFile('web/analysis/THIRD-PARTY-NOTICES.txt',notices);
