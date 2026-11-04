const {chromium}=require('playwright');
const MARK='<path d="M4 16.5c3.5 0 4-9 8-9s4.5 5 8 5"/><path d="M17 10.5l3 2-2 3"/>';
function svg(size,pad,radius){
  // pad = fraction of the canvas kept clear around the mark (maskable needs ~20%)
  const inner=24/(1-2*pad), off=24*pad/(1-2*pad);
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${inner} ${inner}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#12796E"/><stop offset="1" stop-color="#0A564F"/></linearGradient></defs>
  <rect width="${inner}" height="${inner}" rx="${radius?inner*0.22:0}" fill="url(#g)"/>
  <g transform="translate(${off} ${off})" fill="none" stroke="#FFFFFF" stroke-width="2.1"
     stroke-linecap="round" stroke-linejoin="round">${MARK}</g></svg>`;
}
(async()=>{
  const br=await chromium.launch();
  const jobs=[
    ['dist/icon-192.png',192,0.22,true],
    ['dist/icon-512.png',512,0.22,true],
    ['dist/icon-maskable-512.png',512,0.30,false],
    ['dist/apple-touch-icon.png',180,0.20,false],
    ['dist/favicon-32.png',32,0.14,true],
  ];
  for(const [out,size,pad,round] of jobs){
    const ctx=await br.newContext({viewport:{width:size,height:size},deviceScaleFactor:1});
    const p=await ctx.newPage();
    await p.setContent(`<body style="margin:0;background:transparent">${svg(size,pad,round)}</body>`);
    await p.screenshot({path:out,omitBackground:true});
    await ctx.close();
    console.log('wrote',out,size+'px');
  }
  await br.close();
})();
