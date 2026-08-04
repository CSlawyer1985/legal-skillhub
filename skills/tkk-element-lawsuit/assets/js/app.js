// ============================================================
// State
// ============================================================
const state = {
  complaintText: '',
  complaintFile: null,
  templateFile: null,
  caseType: '',
  caseTypeName: '',
  data: {
    plaintiffs: [],
    defendants: [],
    thirds: [],
    agent: {},
    claims: {},
    facts: {},
    jurisdiction: {}
  },
  history: JSON.parse(localStorage.getItem('bude_history') || '[]'),
  currentStep: 1
};

// ============================================================
// Case type map
// ============================================================
const CASE_TYPE_NAMES = {
  lihun: '离婚纠纷', mjjd: '民间借贷纠纷', jrjk: '金融借款合同纠纷',
  maimai: '买卖合同纠纷', ldzy: '劳动争议纠纷', jtsg: '机动车交通事故责任纠纷',
  xyk: '信用卡纠纷', wyfw: '物业服务合同纠纷', bxcss: '财产损失保险合同纠纷',
  zqxjcs: '证券虚假陈述责任纠纷', bzxbx: '保证保险合同纠纷', rongzi: '融资租赁合同纠纷',
  fwmm: '房屋买卖合同纠纷', fwzl: '房屋租赁合同纠纷', jsgc: '建设工程施工合同纠纷',
  rsbx: '人身保险合同纠纷', zebx: '责任保险合同纠纷',
  shangbiao: '侵害商标权纠纷', fmzl: '侵害发明专利权纠纷', wgsj: '侵害外观设计专利权纠纷',
  zhuzuoquan: '侵害著作权及邻接权纠纷', jishu: '技术合同纠纷',
  bzdj: '不正当竞争纠纷', longduan: '垄断纠纷', syms: '侵害商业秘密纠纷',
  hjwr: '环境污染民事公益诉讼', cbpz: '船舶碰撞损害责任纠纷',
  general: '民事纠纷（通用）',
  // 新增类型
  zwxpz: '侵害植物新品种权纠纷', stph: '生态破坏民事公益诉讼', stsh: '生态环境损害赔偿诉讼',
  hsrs: '海上通海水域人身损害责任纠纷', hshyd: '海上通海水域货运代理合同纠纷', cylw: '船员劳务合同纠纷',
  xzcf: '行政处罚', xzqzzx: '行政强制执行', xzxk: '行政许可',
  fwzs: '国有土地上房屋征收决定', gsbx: '工伤保险资格或待遇认定', zfxxgk: '政府信息公开',
  xzfy: '行政复议', xzxy: '行政协议', xzbc: '行政补偿', xzpc: '行政赔偿', xzbllzz: '不履行法定职责',
  sbsqbhfs: '商标申请驳回复审', sbcxfs: '商标撤销复审', sbwx: '商标无效行政',
  zlbhfs: '专利申请驳回复审', zlwx: '专利无效行政', ldzxz: '垄断纠纷行政',
  xswrw: '侮辱案（刑事自诉）', xsfb: '诽谤案（刑事自诉）', xschh: '重婚案（刑事自诉）', xsjbzx: '拒不执行判决裁定案（刑事自诉）',
  zxsqs: '强制执行申请书', jsjczxsqs: '暂时解除飞机高铁限制申请书',
  cyffpz: '参与分配申请书', zxdbsqs: '执行担保申请书', qryxgmqsqs: '确认优先购买权申请书',
  zxyysqs: '执行异议申请书', zxfysqs: '执行复议申请书', zxjdsqs: '执行监督申请书',
  byyxzc: '不予执行仲裁裁决调解书申请书',
  gjpcsqs1: '违法刑事拘留赔偿申请书', gjpcsqs2: '刑事改判无罪赔偿申请书',
  gjpcsqs3: '怠于履行监管职责赔偿申请书', gjpcsqs4: '错误执行赔偿申请书',
};

const TEMPLATE_META = {
  lihun:{title:'民事起诉状（离婚纠纷）', source:'1、离婚纠纷民事起诉状.docx', kind:'民事起诉状'},
  mjjd:{title:'民事起诉状（民间借贷纠纷）', source:'2、民间借贷纠纷民事起诉状.docx', kind:'民事起诉状'},
  jrjk:{title:'民事起诉状（金融借款合同纠纷）', source:'3、金融借款合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  maimai:{title:'民事起诉状（买卖合同纠纷）', source:'4、买卖合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  ldzy:{title:'民事起诉状（劳动争议纠纷）', source:'5、劳动争议纠纷民事起诉状.docx', kind:'民事起诉状'},
  jtsg:{title:'民事起诉状（机动车交通事故责任纠纷）', source:'6、机动车交通事故责任纠纷民事起诉状.docx', kind:'民事起诉状'},
  xyk:{title:'民事起诉状（信用卡纠纷）', source:'7、信用卡纠纷民事起诉状.docx', kind:'民事起诉状'},
  wyfw:{title:'民事起诉状（物业服务合同纠纷）', source:'8、物业服务合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  bxcss:{title:'民事起诉状（财产损失保险合同纠纷）', source:'9、财产损失保险合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  zqxjcs:{title:'民事起诉状（证券虚假陈述责任纠纷）', source:'10、证券虚假陈述责任纠纷民事起诉状.docx', kind:'民事起诉状'},
  bzxbx:{title:'民事起诉状（保证保险合同纠纷）', source:'11、保证保险合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  rongzi:{title:'民事起诉状（融资租赁合同纠纷）', source:'12、融资租赁合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  fwmm:{title:'民事起诉状（房屋买卖合同纠纷）', source:'13、房屋买卖合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  fwzl:{title:'民事起诉状（房屋租赁合同纠纷）', source:'14、房屋租赁合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  jsgc:{title:'民事起诉状（建设工程施工合同纠纷）', source:'15、建设工程施工合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  rsbx:{title:'民事起诉状（人身保险合同纠纷）', source:'16、人身保险合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  zebx:{title:'民事起诉状（责任保险合同纠纷）', source:'17、责任保险合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  zxsqs:{title:'强制执行申请书', source:'18、强制执行申请书.docx', kind:'申请书'},
  jsjczxsqs:{title:'暂时解除乘坐飞机、高铁限制措施申请书', source:'19、暂时解除乘坐飞机、高铁限制措施申请书.docx', kind:'申请书'},
  cyffpz:{title:'参与分配申请书', source:'20、参与分配申请书.docx', kind:'申请书'},
  zxdbsqs:{title:'执行担保申请书', source:'21、执行担保申请书.docx', kind:'申请书'},
  qryxgmqsqs:{title:'确认优先购买权申请书', source:'22、确认优先购买权申请书.docx', kind:'申请书'},
  zxyysqs:{title:'执行异议申请书', source:'23、执行异议申请书.docx', kind:'申请书'},
  zxfysqs:{title:'执行复议申请书', source:'24、执行复议申请书.docx', kind:'申请书'},
  zxjdsqs:{title:'执行监督申请书', source:'25、执行监督申请书.docx', kind:'申请书'},
  byyxzc:{title:'不予执行仲裁裁决、调解书或公证债权文书申请书', source:'26、不予执行仲裁裁决、调解书或公证债权文书申请书.docx', kind:'申请书'},
  xzcf:{title:'行政起诉状（行政处罚）', source:'27、行政处罚行政起诉状.docx', kind:'行政起诉状'},
  xzqzzx:{title:'行政起诉状（行政强制执行）', source:'28、行政强制执行行政起诉状.docx', kind:'行政起诉状'},
  xzxk:{title:'行政起诉状（行政许可）', source:'29、行政许可行政起诉状.docx', kind:'行政起诉状'},
  fwzs:{title:'行政起诉状（国有土地上房屋征收决定）', source:'30、国有土地上房屋征收决定行政起诉状.docx', kind:'行政起诉状'},
  gsbx:{title:'行政起诉状（工伤保险资格或者待遇认定）', source:'31、工伤保险资格或者待遇认定行政起诉状.docx', kind:'行政起诉状'},
  zfxxgk:{title:'行政起诉状（政府信息公开）', source:'32、政府信息公开行政起诉状.docx', kind:'行政起诉状'},
  xzfy:{title:'行政起诉状（行政复议）', source:'33、行政复议行政起诉状.docx', kind:'行政起诉状'},
  xzxy:{title:'行政起诉状（行政协议）', source:'34、行政协议行政起诉状.docx', kind:'行政起诉状'},
  xzbc:{title:'行政起诉状（行政补偿）', source:'35、行政补偿行政起诉状.docx', kind:'行政起诉状'},
  xzpc:{title:'行政起诉状（行政赔偿）', source:'36、行政赔偿行政起诉状.docx', kind:'行政起诉状'},
  xzbllzz:{title:'行政起诉状（不履行法定职责）', source:'37、不履行法定职责行政起诉状.docx', kind:'行政起诉状'},
  xswrw:{title:'刑事（附带民事）自诉状（侮辱案）', source:'38、侮辱案刑事（附带民事）自诉状.docx', kind:'刑事自诉状'},
  xsfb:{title:'刑事（附带民事）自诉状（诽谤案）', source:'39、诽谤案刑事（附带民事）自诉状.docx', kind:'刑事自诉状'},
  xschh:{title:'刑事（附带民事）自诉状（重婚案）', source:'40、重婚案刑事（附带民事）自诉状.docx', kind:'刑事自诉状'},
  xsjbzx:{title:'刑事（附带民事）自诉状（拒不执行判决、裁定案）', source:'41、拒不执行判决、裁定案刑事（附带民事）自诉状.docx', kind:'刑事自诉状'},
  shangbiao:{title:'民事起诉状（侵害商标权纠纷）', source:'42、侵害商标权纠纷民事起诉状.docx', kind:'民事起诉状'},
  fmzl:{title:'民事起诉状（侵害发明专利权纠纷）', source:'43、侵害发明专利权纠纷民事起诉状.docx', kind:'民事起诉状'},
  wgsj:{title:'民事起诉状（侵害外观设计专利权纠纷）', source:'44、侵害外观设计专利权纠纷民事起诉状.docx', kind:'民事起诉状'},
  zwxpz:{title:'民事起诉状（侵害植物新品种权纠纷）', source:'45、侵害植物新品种权纠纷民事起诉状.docx', kind:'民事起诉状'},
  zhuzuoquan:{title:'民事起诉状（侵害著作权及邻接权纠纷）', source:'46、侵害著作权及邻接权纠纷民事起诉状.docx', kind:'民事起诉状'},
  jishu:{title:'民事起诉状（技术合同纠纷）', source:'47、技术合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  bzdj:{title:'民事起诉状（不正当竞争纠纷）', source:'48、不正当竞争纠纷民事起诉状.docx', kind:'民事起诉状'},
  longduan:{title:'民事起诉状（垄断纠纷）', source:'49、垄断纠纷民事起诉状.docx', kind:'民事起诉状'},
  syms:{title:'民事起诉状（侵害商业秘密纠纷）', source:'50、侵害商业秘密纠纷民事起诉状.docx', kind:'民事起诉状'},
  sbsqbhfs:{title:'行政起诉状（商标申请驳回复审）', source:'51、商标申请驳回复审纠纷行政起诉状.docx', kind:'行政起诉状'},
  sbcxfs:{title:'行政起诉状（商标撤销复审）', source:'52、商标撤销复审行政纠纷行政起诉状.docx', kind:'行政起诉状'},
  sbwx:{title:'行政起诉状（商标无效行政纠纷）', source:'53、商标无效行政纠纷行政起诉状.docx', kind:'行政起诉状'},
  zlbhfs:{title:'行政起诉状（专利申请驳回复审行政纠纷）', source:'54、专利申请驳回复审行政纠纷行政起诉状.docx', kind:'行政起诉状'},
  zlwx:{title:'行政起诉状（专利无效行政纠纷）', source:'55、专利无效行政纠纷行政起诉状.docx', kind:'行政起诉状'},
  ldzxz:{title:'行政起诉状（垄断纠纷）', source:'56、垄断纠纷行政起诉状.docx', kind:'行政起诉状'},
  hjwr:{title:'民事起诉状（环境污染民事公益诉讼）', source:'57、环境污染民事公益诉讼民事起诉状.docx', kind:'民事起诉状'},
  stph:{title:'民事起诉状（生态破坏民事公益诉讼）', source:'58、生态破坏民事公益诉讼民事起诉状.docx', kind:'民事起诉状'},
  stsh:{title:'民事起诉状（生态环境损害赔偿诉讼）', source:'59、生态环境损害赔偿诉讼民事起诉状.docx', kind:'民事起诉状'},
  gjpcsqs1:{title:'国家赔偿申请书（违法刑事拘留赔偿）', source:'60、违法刑事拘留赔偿国家赔偿申请书.docx', kind:'国家赔偿申请书'},
  gjpcsqs2:{title:'国家赔偿申请书（刑事改判无罪赔偿）', source:'61、刑事改判无罪赔偿国家赔偿申请书.docx', kind:'国家赔偿申请书'},
  gjpcsqs3:{title:'国家赔偿申请书（怠于履行监管职责致伤致死赔偿）', source:'62、怠于履行监管职责致伤致死赔偿国家赔偿申请书.docx', kind:'国家赔偿申请书'},
  gjpcsqs4:{title:'国家赔偿申请书（错误执行赔偿）', source:'63、错误执行赔偿国家赔偿申请书.docx', kind:'国家赔偿申请书'},
  cbpz:{title:'民事起诉状（船舶碰撞损害责任纠纷）', source:'64、船舶碰撞损害责任纠纷民事起诉状.docx', kind:'民事起诉状'},
  hsrs:{title:'民事起诉状（海上、通海水域人身损害责任纠纷）', source:'65、海上、通海水域人身损害责任纠纷民事起诉状.docx', kind:'民事起诉状'},
  hshyd:{title:'民事起诉状（海上、通海水域货运代理合同纠纷）', source:'66、海上、通海水域货运代理合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  cylw:{title:'民事起诉状（船员劳务合同纠纷）', source:'67、船员劳务合同纠纷民事起诉状.docx', kind:'民事起诉状'},
  general:{title:'民事起诉状（通用）', source:'内置通用模板', kind:'民事起诉状'}
};

function getCurrentTemplateMeta() {
  const meta = TEMPLATE_META[state.caseType] || TEMPLATE_META.general;
  const title = meta.title || ('民事起诉状（' + (state.caseTypeName || '通用') + '）');
  const isApply = /申请书/.test(title) || /申请书/.test(meta.kind || '');
  return {
    ...meta,
    title,
    requestHeader: isApply ? '申请事项' : '诉讼请求',
    factHeader: '事实与理由',
    lockTip: '已按对应要素式范本锁定栏目顺序、字段名称与呈现层级；工具仅填充值，不对范本结构做增删改。'
  };
}

function updateTemplateMetaCard() {
  const card = document.getElementById('template-meta-card');
  if (!card) return;
  if (!state.caseType) { card.style.display = 'none'; return; }
  const meta = getCurrentTemplateMeta();
  card.style.display = 'block';
  document.getElementById('template-meta-title').textContent = meta.title;
  document.getElementById('template-meta-sub').textContent = meta.lockTip;
  document.getElementById('template-meta-dockind').textContent = meta.kind || '-';
  document.getElementById('template-meta-source').textContent = meta.source || '-';
}

function onCaseTypeChange(value) {
  state.caseType = value;
  state.caseTypeName = CASE_TYPE_NAMES[value] || '民事纠纷（通用）';
  const fc = document.getElementById('claims-fields-container');
  const ff = document.getElementById('facts-fields-container');
  if (fc && ff) { buildClaimsSection(); buildFactsSection(); }
  updateTemplateMetaCard();
}

function validateTemplateCompleteness() {
  const errors = [];
  if (!state.caseType) errors.push('未选择案件类型');
  if (!state.data?.plaintiffs?.length) errors.push('原告信息未完整识别');
  if (!state.data?.defendants?.length) errors.push('被告信息未完整识别');
  const claimDefs = getClaimFields(state.caseType || 'general') || [];
  const factDefs = getFactsFields(state.caseType || 'general') || [];
  const hasAnyClaim = claimDefs.some(([k]) => (state.data?.claims?.[k] || '').trim());
  const hasAnyFact = factDefs.some(([k]) => (state.data?.facts?.[k] || '').trim());
  if (!hasAnyClaim) errors.push('诉请/申请事项尚未填写');
  if (!hasAnyFact) errors.push('事实与理由尚未填写');
  return errors;
}

// ============================================================
// Step navigation
// ============================================================
function goStep(n) {
  if (n < state.currentStep && n !== state.currentStep) {
    // Allow going back
  }
  document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
  document.getElementById('step-' + n).classList.add('active');
  document.querySelectorAll('.step-item').forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i + 1 < n) el.classList.add('done');
    if (i + 1 === n) el.classList.add('active');
  });
  state.currentStep = n;
  window.scrollTo({top: 0, behavior: 'smooth'});
}

// ============================================================
// File upload
// ============================================================
function handleDrop(e, type) {
  e.preventDefault();
  document.getElementById('zone-' + (type === 'complaint' ? 'complaint' : 'template')).classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file) processFile(file, type);
}

function handleFileSelect(e, type) {
  const file = e.target.files[0];
  if (file) processFile(file, type);
}

async function processFile(file, type) {
  if (file.size > 20 * 1024 * 1024) {
    showToast('文件大小超过 20MB 限制', 'error');
    return;
  }
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['docx','pdf'].includes(ext)) {
    showToast('仅支持 .docx 和 .pdf 格式', 'error');
    return;
  }

  const zone = document.getElementById('zone-' + (type === 'complaint' ? 'complaint' : 'template'));
  const nameEl = document.getElementById(type === 'complaint' ? 'complaint-name' : 'template-name');

  zone.classList.add('has-file');
  nameEl.textContent = '✓ ' + file.name;

  if (type === 'complaint') {
    state.complaintFile = file;
    showProgress('complaint', true);
    try {
      state.complaintText = await extractText(file);
      showProgress('complaint', false);
      document.getElementById('btn-analyze').disabled = false;
      showToast('文件读取成功，共 ' + state.complaintText.length + ' 字', 'success');
    } catch(e) {
      showProgress('complaint', false);
      showToast('文件读取失败：' + e.message, 'error');
      zone.classList.remove('has-file');
      nameEl.textContent = '';
    }
  } else {
    state.templateFile = file;
    showToast('范本上传成功', 'success');
  }
}

function showProgress(type, show) {
  const el = document.getElementById(type + '-progress');
  if (el) el.style.display = show ? 'block' : 'none';
  if (show) {
    let w = 0;
    const bar = document.getElementById(type + '-bar');
    const t = setInterval(() => { w = Math.min(w + Math.random() * 15, 90); bar.style.width = w + '%'; if (w >= 90) clearInterval(t); }, 150);
  }
}

async function extractText(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (ext === 'docx') {
    const buf = await file.arrayBuffer();
    const result = await mammoth.extractRawText({arrayBuffer: buf});
    return result.value;
  } else if (ext === 'pdf') {
    // For PDFs, use FileReader to get text (basic extraction)
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          // Try basic PDF text extraction via fetch trick
          const text = await extractPdfText(e.target.result);
          resolve(text);
        } catch(err) {
          reject(new Error('PDF 解析失败，建议将文件转换为 docx 格式后重试'));
        }
      };
      reader.onerror = () => reject(new Error('文件读取失败'));
      reader.readAsArrayBuffer(file);
    });
  }
  throw new Error('不支持的文件格式');
}

async function extractPdfText(arrayBuffer) {
  // Simple text extraction from PDF bytes (ASCII readable portions)
  const bytes = new Uint8Array(arrayBuffer);
  let text = '';
  const decoder = new TextDecoder('utf-8', {fatal: false});
  const chunk = decoder.decode(bytes);
  // Extract text between BT and ET markers
  const matches = chunk.matchAll(/\(([^)]{1,200})\)\s*Tj/g);
  for (const m of matches) {
    text += m[1] + '\n';
  }
  if (!text.trim()) {
    throw new Error('PDF 文本提取失败');
  }
  return text;
}

// ============================================================
// AI Analysis
// ============================================================
async function startAnalyze() {
  const aiConfig = getAiConfig();
  const apiKey = aiConfig.apiKey;
  if (!apiKey) {
    showToast('请先输入阿里云百炼 API Key', 'error');
    return;
  }
  if (!state.complaintText) {
    showToast('请先上传起诉状文件', 'error');
    return;
  }

  document.getElementById('loading-overlay').classList.add('visible');
  const lsub = document.getElementById('loading-sub-text');
  if (lsub) { const found = (typeof AI_MODELS!=='undefined') ? AI_MODELS.flatMap(g=>g.items).find(m=>m.value===selectedModel) : null; lsub.textContent = '正在调用 ' + (found?found.label:selectedModel||'AI 模型') + '，请稍候'; }
  setLoadingStep(1);

  try {
    // Step 1: parse done
    setLoadingStep(2);

    // 步骤2+3 并行发起：当事人识别 & 要素提取同时进行
    // 先拿 partiesResult（含caseType），再并行时把caseType传给facts
    // 由于是Promise.all同时发起，parties先完成后用其caseType提示facts
    // 但两者同时发起无法传递——改为：parties完成后才发facts（串行）以获得更准确的字段匹配
    const partiesResult = await callBailianParties(apiKey, state.complaintText);
    setLoadingStep(3);
    // 用已识别的案件类型来精准提取对应字段
    const resolvedType = (document.getElementById('caseType')?.value) || (partiesResult.caseType || 'general');
    const factsResult = await callBailianFacts(apiKey, state.complaintText, resolvedType);
    setLoadingStep(4);
    await delay(100);

    // 合并两次结果
    const extracted = Object.assign({}, partiesResult, factsResult);

    populateState(extracted);

    // caseType already set by populateState(); just sync selector UI
    const sel = document.getElementById('caseType');
    if (sel && state.caseType) sel.value = state.caseType;

    document.getElementById('loading-overlay').classList.remove('visible');

    // Build edit UI
    buildEditUI();
    // 标注推断字段
    setTimeout(() => {
      // 如果开启了推断，对所有动态字段中有值的都标注（AI已按字段列表精准填写）
      const inferOn = document.getElementById('inferToggle')?.checked !== false;
      if (inferOn) {
        // 扫描所有动态facts和claim字段，有值的都加标注（AI推断填写的）
        document.querySelectorAll('#step-3 [id^="fact-"], #step-3 [id^="claim-field-"]').forEach(el => {
          if (el.value && el.value.trim()) {
            el.classList.add('inferred');
            const label = el.closest('.fact-field')?.querySelector('.fact-label');
            if (label && !label.querySelector('.inferred-badge')) {
              label.insertAdjacentHTML('beforeend', '<span class="inferred-badge">AI填写</span>');
            }
          }
        });
      }
    }, 100);
    goStep(3);

    // Add to history
    addHistory({
      name: state.complaintFile?.name || '未知文件',
      caseType: state.caseTypeName,
      parties: state.data.plaintiffs.length + ' 原告 / ' + state.data.defendants.length + ' 被告',
      time: new Date().toLocaleString('zh-CN'),
      status: 'success'
    });

    showToast('AI 分析完成，识别到 ' + state.data.plaintiffs.length + ' 位原告、' + state.data.defendants.length + ' 位被告', 'success');

  } catch(e) {
    document.getElementById('loading-overlay').classList.remove('visible');
    showToast('AI 分析失败：' + e.message, 'error');
    addHistory({
      name: state.complaintFile?.name || '未知文件',
      caseType: '-',
      parties: '-',
      time: new Date().toLocaleString('zh-CN'),
      status: 'error'
    });
  }
}

function setLoadingStep(n) {
  for (let i = 1; i <= 4; i++) {
    const el = document.getElementById('ls-' + i);
    if (!el) continue;
    const texts = ['文件解析', '当事人识别', '要素提取', '生成表格结构'];
    if (i < n) { el.className = 'loading-step done'; el.textContent = '✅ ' + texts[i-1]; }
    else if (i === n) { el.className = 'loading-step current'; el.textContent = '⏳ ' + texts[i-1]; }
    else { el.className = 'loading-step'; el.textContent = '⬜ ' + texts[i-1]; }
  }
}

function delay(ms) { return new Promise(r => setTimeout(r, ms)); }

// ============================================================
// Bailian API Call
// ============================================================
// ──────────────────────────────────────────────────────────
// 工具函数：调用百炼 API（通用）
// ──────────────────────────────────────────────────────────
async function _fetchBailian(apiKey, prompt, maxTokens) {
  const aiConfig = getAiConfig();
  const endpoint = aiConfig.baseUrl || 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions';
  const model = aiConfig.model || 'qwen-plus';
  const resp = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ' + apiKey
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.1,
      max_tokens: maxTokens
    })
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error?.message || err.message || 'API 调用失败 (HTTP ' + resp.status + ')');
  }
  const json = await resp.json();
  const content = json.choices?.[0]?.message?.content || '';
  const cleaned = content.replace(/```json\n?/g,'').replace(/```\n?/g,'').trim();
  try {
    return JSON.parse(cleaned);
  } catch(e) {
    const m = cleaned.match(/\{[\s\S]*\}/);
    if (m) return JSON.parse(m[0]);
    throw new Error('AI 返回格式异常，无法解析');
  }
}

// ──────────────────────────────────────────────────────────
// 第一次调用：当事人识别（prompt 精简，速度快）
// 只提取：caseType、court、plaintiffs、defendants、thirds、agent
// ──────────────────────────────────────────────────────────
async function callBailianParties(apiKey, text) {
  // 只取前3000字，当事人信息一般在起诉状头部
  const trimText = text.slice(0, 3000);

  const prompt = `你是律师助理，请从起诉状文本中只提取当事人信息，严格输出JSON，不要输出其他任何内容。

起诉状文本：
---
${trimText}
---

输出格式：
{
  "caseType": "（案件类型代码，必须从下表精确匹配，输出code，不得自创：
【民事-合同类】mjjd=民间借贷纠纷 | jrjk=金融借款合同纠纷 | maimai=买卖合同纠纷 | fwmm=房屋买卖合同纠纷 | fwzl=房屋租赁合同纠纷 | jsgc=建设工程施工合同纠纷 | wyfw=物业服务合同纠纷 | xyk=信用卡纠纷 | rongzi=融资租赁合同纠纷 | jishu=技术合同纠纷 | hshyd=海上通海水域货运代理合同纠纷 | cylw=船员劳务合同纠纷
【民事-侵权/人身类】lihun=离婚纠纷 | ldzy=劳动争议纠纷 | jtsg=机动车交通事故责任纠纷 | hsrs=海上通海水域人身损害责任纠纷 | cbpz=船舶碰撞损害责任纠纷
【民事-保险类】bxcss=财产损失保险合同纠纷 | bzxbx=保证保险合同纠纷 | rsbx=人身保险合同纠纷 | zebx=责任保险合同纠纷
【民事-知识产权类】shangbiao=侵害商标权纠纷 | fmzl=侵害发明专利权纠纷 | wgsj=侵害外观设计专利权纠纷 | zwxpz=侵害植物新品种权纠纷 | zhuzuoquan=侵害著作权及邻接权纠纷 | bzdj=不正当竞争纠纷 | longduan=垄断纠纷 | syms=侵害商业秘密纠纷
【民事-公益诉讼】hjwr=环境污染民事公益诉讼 | stph=生态破坏民事公益诉讼 | stsh=生态环境损害赔偿诉讼
【民事-证券】zqxjcs=证券虚假陈述责任纠纷
【行政诉讼】xzcf=行政处罚 | xzqzzx=行政强制执行 | xzxk=行政许可 | fwzs=国有土地上房屋征收决定 | gsbx=工伤保险资格或待遇认定 | zfxxgk=政府信息公开 | xzfy=行政复议 | xzxy=行政协议 | xzbc=行政补偿 | xzpc=行政赔偿 | xzbllzz=不履行法定职责 | sbsqbhfs=商标申请驳回复审 | sbcxfs=商标撤销复审 | sbwx=商标无效 | zlbhfs=专利申请驳回复审 | zlwx=专利无效 | ldzxz=垄断纠纷行政
【刑事自诉】xswrw=侮辱案 | xsfb=诽谤案 | xschh=重婚案 | xsjbzx=拒不执行判决裁定案
【执行类申请书】zxsqs=强制执行申请书 | jsjczxsqs=暂时解除飞机高铁限制申请书 | cyffpz=参与分配申请书 | zxdbsqs=执行担保申请书 | qryxgmqsqs=确认优先购买权申请书 | zxyysqs=执行异议申请书 | zxfysqs=执行复议申请书 | zxjdsqs=执行监督申请书 | byyxzc=不予执行仲裁裁决调解书申请书
【国家赔偿申请书】gjpcsqs1=违法刑事拘留赔偿 | gjpcsqs2=刑事改判无罪赔偿 | gjpcsqs3=怠于履行监管职责赔偿 | gjpcsqs4=错误执行赔偿
【general=其他民事纠纷通用（无法匹配以上任何类型时才使用）】
注意：知识产权纠纷绝对不能识别为民间借贷，行政案件绝对不能识别为民事合同纠纷）"，
  "caseTypeName": "（案件类型名称）",
  "court": "（受诉法院）",
  "plaintiffs": [{"type":"person或org","name":"","gender":"","birth":"","nation":"","idType":"","idNum":"","addr":"","habitual":"","phone":"","work":"","job":"","legalRep":"","creditCode":"","regAddr":"","orgType":"","ownership":""}],
  "defendants": [（同上）],
  "thirds": [（同上）],
  "agent": {"has":false,"name":"","job":"","firm":"","phone":"","auth":""}
}

注意：未记载的字段留空字符串，只输出JSON。
额外要求：1. 只能填写当前模板提供的claims和facts字段；2. 没有明确事实支撑的字段留空；3. 不得把传统起诉状中的自由表述改写为新的字段标题；4. 不得输出模板之外的key。`;

  return _fetchBailian(apiKey, prompt, 1500);
}

// ──────────────────────────────────────────────────────────
// 第二次调用：要素提取（诉讼请求 + 事实与理由 + 管辖）
// ──────────────────────────────────────────────────────────
async function callBailianFacts(apiKey, text, caseType) {
  const trimText = text.slice(0, 7000);
  const inferEnabled = document.getElementById('inferToggle')?.checked !== false;

  // 动态构建JSON字段模板：根据案件类型，把对应的字段key和标签传给AI
  // 严格范本模式：只能对当前模板既有字段填值，不得改名、合并、拆分、补造新字段。
  const cType = caseType || 'general';
  const claimFieldDefs = getClaimFields(cType);
  const factsFieldDefs = getFactsFields(cType);

  // 生成claims JSON模板（key: "字段标签（请填写）"）
  const claimsTemplate = Object.fromEntries(
    [['full','（诉讼请求完整内容）'],['total','（标的总额）'],['lawyerFee','no'],['preservation','no'],
     ...claimFieldDefs.map(([k,l]) => [k, ''])]
  );
  const factsTemplate = Object.fromEntries(
    factsFieldDefs.map(([k,l]) => [k, ''])
  );

  // 生成字段说明列表，让AI知道每个key对应什么含义
  // 字段说明：结构化hint字段传格式模板，普通字段只传名称
  function isStructured(hint) {
    if (!hint) return false;
    const matches = (hint.match(/[\u4e00-\u9fff]{1,8}[（(]?[\u4e00-\u9fff]*[）)]?\s*[：:]/g) || []);
    return matches.length >= 2;
  }
  function fieldDesc(k, l, h) {
    const cleanLabel = l.replace(/^【.*?】/, '').trim();
    if (h && isStructured(h)) {
      // 结构化字段：传入模板，要求AI按格式填写
      const template = h.replace(/\n/g, '\\n').replace(/"/g, '\\"').slice(0, 500);
      return `  "${k}": "${cleanLabel}（请严格按以下格式填写，把提取到的信息填入冒号后，□为勾选项按实际打✓，无法确认的留空）：\\n${template}"`;
    }
    return `  "${k}": "${cleanLabel}"`;
  }
  const claimDesc = claimFieldDefs.map(([k,l,h]) => fieldDesc(k,l,h)).join(',\n');
  const factsDesc = factsFieldDefs.map(([k,l,h]) => fieldDesc(k,l,h)).join(',\n');

  const inferInstruction = inferEnabled ? `

【推断填写规则】对于事实与理由中可从文意推断的字段，直接填写结论，不加任何前缀和理由：
- 到期/逾期情况：结合到期日和起诉日期，判断是否逾期、逾期多久或尚未到期
- 违约情形：综合文意推断违约形态（拒付/迟延/部分履行/根本违约等）
- 催告情况：如有"多次要求""催款""催告"等表述，提炼填写
- 履行情况：结合已付/欠付金额综合描述
- 是否主张律师费：诉请中出现"律师费"则lawyerFee填yes，否则no
- 是否诉前保全：有保全申请或查封冻结则preservation填yes，否则no
- 标的总额：尽量从各诉请项目求和计算填写` : '';

  const prompt = `你是资深律师助理，请从起诉状文本中精准提取要素信息，严格输出JSON。${inferInstruction}

起诉状文本：
---
${trimText}
---

本案类型：${cType}

【重要规则】
1. 输出JSON中，结构化格式字段已预填了格式模板（含\n换行），请保持模板结构不变，只把从起诉状提取到的信息填入对应冒号后的空白位置，□勾选项根据实际情况替换为✓（已选）或□（未选），无法确认的保留空白
2. 没有格式说明的字段，直接输出从起诉状提取的简洁内容
3. 如果起诉状文本中没有对应信息，留空字符串""
4. 不要重复字段名称本身，不要照抄大段无关文字

请按以下字段提取（字段名称说明）：

诉讼请求字段：
${claimDesc}

事实与理由字段：
${factsDesc}

输出JSON（只输出JSON，不要其他内容）：
{
  "claims": {
    "full": "","total": "","lawyerFee": "no","preservation": "no",
${claimFieldDefs.map(([k,l,h]) => { const v = (h && isStructured(h)) ? h.replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\n/g,'\\n') : ''; return `    "${k}": "${v}"`; }).join(',\n')}
  },
  "facts": {
${factsFieldDefs.map(([k,l,h]) => { const v = (h && isStructured(h)) ? h.replace(/\\/g,'\\\\').replace(/"/g,'\\"').replace(/\n/g,'\\n') : ''; return `    "${k}": "${v}"`; }).join(',\n')}
  },
  "jurisdiction": {"court": "","basis": "","mediation": "no"},
  "missingFields": []
}`;

  return _fetchBailian(apiKey, prompt, 3000);
}

// ============================================================
// Populate state from AI result
// ============================================================
function populateState(extracted) {
  // Ensure arrays
  state.data.plaintiffs = (extracted.plaintiffs || []).map(normalizeParty);
  state.data.defendants = (extracted.defendants || []).map(normalizeParty);
  state.data.thirds = (extracted.thirds || []).map(normalizeParty);

  // Default to at least empty entries
  if (state.data.plaintiffs.length === 0) state.data.plaintiffs.push({type:'person',name:'',_id:uid()});
  if (state.data.defendants.length === 0) state.data.defendants.push({type:'person',name:'',_id:uid()});

  state.data.agent = extracted.agent || {};
  state.data.claims = extracted.claims || {};
  state.data.facts = extracted.facts || {};
  state.data.jurisdiction = extracted.jurisdiction || {};
  state.data.missingFields = extracted.missingFields || [];

  const courtEl2 = document.getElementById('court'); if (extracted.court && courtEl2) courtEl2.value = extracted.court;
  // Set caseType - 手动选择 > AI识别 > general
  const aiType = (extracted.caseType || '').trim().toLowerCase();
  const selEl = document.getElementById('caseType');
  const manualType = (selEl && selEl.value) ? selEl.value : '';
  // 手动选择的类型优先；AI只在用户未选时生效
  state.caseType = manualType || aiType || 'general';
  state.caseTypeName = CASE_TYPE_NAMES[state.caseType] || extracted.caseTypeName || '民事纠纷（通用）';
  // Auto-build facts_parties if AI returned generic "原告/被告" text
  if (state.data.facts) {
    const fp = state.data.facts.facts_parties || '';
    if (!fp || fp.includes('原告') && !fp.includes('与')) {
      // Build from actual party names
      const pNames = state.data.plaintiffs.map(p=>p.name).filter(Boolean);
      const dNames = state.data.defendants.map(p=>p.name).filter(Boolean);
      if (pNames.length && dNames.length) {
        state.data.facts.facts_parties = pNames.join('、') + '与' + dNames.join('、');
      }
    }
    // Also auto-build facts_contract signing parties for common fields
    ['facts_parties','facts_contract'].forEach(key => {
      if (state.data.facts[key]) {
        // Replace "原告" with actual name if only one plaintiff
        if (state.data.plaintiffs.length === 1 && state.data.plaintiffs[0].name) {
          state.data.facts[key] = state.data.facts[key].replace(/^原告(?=[与、]|$)/, state.data.plaintiffs[0].name);
        }
      }
    });
  }
  // Debug log
  console.log('[BUDE] AI returned caseType:', extracted.caseType, '→ final:', state.caseType, state.caseTypeName);
}

function inferFromIdNum(idNum) {
  // Chinese 18-digit ID card: positions 7-14 = birthdate, position 17 = gender (odd=male)
  if (!idNum || idNum.length !== 18) return {};
  const y = idNum.slice(6,10), m = idNum.slice(10,12), d = idNum.slice(12,14);
  const birth = y + '年' + parseInt(m) + '月' + parseInt(d) + '日';
  const gender = (parseInt(idNum[16]) % 2 === 1) ? '男' : '女';
  return { birth, gender };
}

function normalizeParty(p) {
  // Infer gender and birth from ID number if not provided
  const inferred = (p.type === 'person' || !p.type) ? inferFromIdNum(p.idNum) : {};
  return { type: p.type||'person', name:p.name||'',
    gender: p.gender || inferred.gender || '',
    birth: p.birth || inferred.birth || '',
    nation:p.nation||'', idType:p.idType||'', idNum:p.idNum||'', addr:p.addr||'',
    habitual:p.habitual||'', phone:p.phone||'', work:p.work||'', job:p.job||'',
    legalRep:p.legalRep||'', creditCode:p.creditCode||'', regAddr:p.regAddr||'',
    orgType:p.orgType||'', ownership:p.ownership||'', _id: uid() };
}

function uid() { return Math.random().toString(36).slice(2, 9); }

// ============================================================
// Build edit UI
// ============================================================
function buildEditUI() {
  buildPartySection('plaintiffs');
  buildPartySection('defendants');
  buildPartySection('thirds');
  buildAgentSection();
  buildClaimsSection();
  buildFactsSection();
  buildJurisdictionSection();
  updateBadges();

  if (state.data.missingFields && state.data.missingFields.length) {
    const notice = document.getElementById('missing-notice');
    notice.style.display = 'flex';
    document.getElementById('missing-text').textContent = '以下字段未能从文书中确认，请手动补充：' + state.data.missingFields.join('、');
  }
}

function buildPartySection(role) {
  const container = document.getElementById(role + '-container');
  container.innerHTML = '';
  state.data[role].forEach((p, i) => {
    container.appendChild(createPartyCard(role, i, p));
  });
}

function createPartyCard(role, index, info) {
  const roleNames = {plaintiffs:'原告', defendants:'被告', thirds:'第三人'};
  const div = document.createElement('div');
  div.className = 'party-card';
  div.id = 'party-' + role + '-' + (info._id || index);

  const isPerson = (info.type || 'person') === 'person';
  const roleLabel = roleNames[role] + (state.data[role].length > 1 ? '（' + (index+1) + '）' : '');

  div.innerHTML = `
    <div class="party-card-header">
      <div class="party-card-title">
        ${roleLabel}
        <div class="type-toggle">
          <button class="type-toggle-btn ${isPerson ? 'active' : ''}" onclick="togglePartyType('${role}',${index},'person')">自然人</button>
          <button class="type-toggle-btn ${!isPerson ? 'active' : ''}" onclick="togglePartyType('${role}',${index},'org')">法人/组织</button>
        </div>
      </div>
      ${state.data[role].length > 1 ? `<button class="btn btn-danger" onclick="removeParty('${role}',${index})">删除</button>` : ''}
    </div>
    <div class="party-card-body">
      ${isPerson ? renderPersonFields(role, index, info) : renderOrgFields(role, index, info)}
    </div>
  `;
  return div;
}

function renderPersonFields(role, index, info) {
  const p = (field) => `${role}_${index}_${field}`;
  return `
    <div class="field-grid">
      <div class="field-group">
        <label class="field-label">姓名 *</label>
        <input type="text" class="field-input ${!info.name ? 'missing' : ''}" id="${p('name')}" value="${esc(info.name)}" placeholder="请填写姓名" oninput="saveField('${role}',${index},'name',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">性别</label>
        <div class="gender-group">
          <label class="gender-option"><input type="radio" name="${p('gender')}" value="男" ${info.gender==='男'?'checked':''} onchange="saveField('${role}',${index},'gender','男')"> 男</label>
          <label class="gender-option"><input type="radio" name="${p('gender')}" value="女" ${info.gender==='女'?'checked':''} onchange="saveField('${role}',${index},'gender','女')"> 女</label>
        </div>
      </div>
      <div class="field-group">
        <label class="field-label">出生日期</label>
        <input type="text" class="field-input" id="${p('birth')}" value="${esc(info.birth)}" placeholder="如：1990年1月1日" oninput="saveField('${role}',${index},'birth',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">民族</label>
        <input type="text" class="field-input" id="${p('nation')}" value="${esc(info.nation)}" placeholder="如：汉族" oninput="saveField('${role}',${index},'nation',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">证件类型</label>
        <select class="field-input" id="${p('idType')}" onchange="saveField('${role}',${index},'idType',this.value)">
          <option value="">-- 请选择 --</option>
          <option ${info.idType==='居民身份证'?'selected':''}>居民身份证</option>
          <option ${info.idType==='护照'?'selected':''}>护照</option>
          <option ${info.idType==='港澳通行证'?'selected':''}>港澳通行证</option>
          <option ${info.idType==='台湾通行证'?'selected':''}>台湾通行证</option>
          <option ${info.idType==='其他'?'selected':''}>其他</option>
        </select>
      </div>
      <div class="field-group">
        <label class="field-label">证件号码</label>
        <input type="text" class="field-input" id="${p('idNum')}" value="${esc(info.idNum)}" placeholder="证件号码" oninput="saveField('${role}',${index},'idNum',this.value)">
      </div>
      <div class="field-group" style="grid-column: 1/-1;">
        <label class="field-label">住所地（户籍所在地）*</label>
        <input type="text" class="field-input ${!info.addr ? 'missing' : ''}" id="${p('addr')}" value="${esc(info.addr)}" placeholder="请填写户籍所在地" oninput="saveField('${role}',${index},'addr',this.value)">
      </div>
      <div class="field-group" style="grid-column: 1/-1;">
        <label class="field-label">经常居住地（与户籍不同时填写）</label>
        <input type="text" class="field-input" id="${p('habitual')}" value="${esc(info.habitual)}" placeholder="经常居住地" oninput="saveField('${role}',${index},'habitual',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">联系电话</label>
        <input type="text" class="field-input" id="${p('phone')}" value="${esc(info.phone)}" placeholder="联系电话" oninput="saveField('${role}',${index},'phone',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">工作单位</label>
        <input type="text" class="field-input" id="${p('work')}" value="${esc(info.work)}" placeholder="工作单位" oninput="saveField('${role}',${index},'work',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">职务</label>
        <input type="text" class="field-input" id="${p('job')}" value="${esc(info.job)}" placeholder="职务" oninput="saveField('${role}',${index},'job',this.value)">
      </div>
    </div>`;
}

function renderOrgFields(role, index, info) {
  const p = (field) => `${role}_${index}_${field}`;
  return `
    <div class="field-grid">
      <div class="field-group" style="grid-column:1/-1;">
        <label class="field-label">名称 *</label>
        <input type="text" class="field-input ${!info.name ? 'missing' : ''}" id="${p('name')}" value="${esc(info.name)}" placeholder="企业/机构全称" oninput="saveField('${role}',${index},'name',this.value)">
      </div>
      <div class="field-group" style="grid-column:1/-1;">
        <label class="field-label">住所地（主要办事机构所在地）*</label>
        <input type="text" class="field-input ${!info.addr ? 'missing' : ''}" id="${p('addr')}" value="${esc(info.addr)}" placeholder="住所地" oninput="saveField('${role}',${index},'addr',this.value)">
      </div>
      <div class="field-group" style="grid-column:1/-1;">
        <label class="field-label">注册地/登记地</label>
        <input type="text" class="field-input" id="${p('regAddr')}" value="${esc(info.regAddr)}" placeholder="注册地" oninput="saveField('${role}',${index},'regAddr',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">法定代表人/负责人</label>
        <input type="text" class="field-input" id="${p('legalRep')}" value="${esc(info.legalRep)}" placeholder="法定代表人姓名" oninput="saveField('${role}',${index},'legalRep',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">职务</label>
        <input type="text" class="field-input" id="${p('job')}" value="${esc(info.job)}" placeholder="如：法定代表人" oninput="saveField('${role}',${index},'job',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">联系电话</label>
        <input type="text" class="field-input" id="${p('phone')}" value="${esc(info.phone)}" placeholder="联系电话" oninput="saveField('${role}',${index},'phone',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">统一社会信用代码</label>
        <input type="text" class="field-input" id="${p('creditCode')}" value="${esc(info.creditCode)}" placeholder="18位统一社会信用代码" oninput="saveField('${role}',${index},'creditCode',this.value)">
      </div>
      <div class="field-group">
        <label class="field-label">组织类型</label>
        <select class="field-input" id="${p('orgType')}" onchange="saveField('${role}',${index},'orgType',this.value)">
          <option value="">-- 请选择 --</option>
          <option ${info.orgType==='有限责任公司'?'selected':''}>有限责任公司</option>
          <option ${info.orgType==='股份有限公司'?'selected':''}>股份有限公司</option>
          <option ${info.orgType==='上市公司'?'selected':''}>上市公司</option>
          <option ${info.orgType==='国有企业'?'selected':''}>国有企业</option>
          <option ${info.orgType==='非法人组织'?'selected':''}>非法人组织</option>
          <option ${info.orgType==='其他企业法人'?'selected':''}>其他企业法人</option>
        </select>
      </div>
      <div class="field-group">
        <label class="field-label">所有制性质</label>
        <select class="field-input" id="${p('ownership')}" onchange="saveField('${role}',${index},'ownership',this.value)">
          <option value="">-- 请选择 --</option>
          <option ${info.ownership==='国有（控股）'?'selected':''}>国有（控股）</option>
          <option ${info.ownership==='国有（参股）'?'selected':''}>国有（参股）</option>
          <option ${info.ownership==='民营'?'selected':''}>民营</option>
          <option ${info.ownership==='外资'?'selected':''}>外资</option>
          <option ${info.ownership==='其他'?'selected':''}>其他</option>
        </select>
      </div>
    </div>`;
}

function buildAgentSection() {
  const a = state.data.agent || {};
  const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.value = val; };
  const setChk = (id, val) => { const el = document.getElementById(id); if (el) el.checked = val; };
  if (a.has) {
    setChk('agent-yes', true);
    const af = document.getElementById('agent-fields');
    if (af) af.style.display = 'block';
  }
  if (a.name) setVal('agent-name', a.name);
  if (a.job) setVal('agent-job', a.job);
  if (a.firm) setVal('agent-firm', a.firm);
  if (a.phone) setVal('agent-phone', a.phone);
  if (a.auth === 'special') setChk('auth-special', true);
}

function buildClaimsSection() {
  const c = state.data.claims || {};
  // Rebuild dynamic claim fields based on case type
  const container = document.getElementById('claims-fields-container');
  if (container) {
    container.innerHTML = '';
    const claimFields = getClaimFields(state.caseType);
    claimFields.forEach(([key, label, hint]) => {
      const val = c[key] || '';
      const displayLbl = label.replace(/^【.*?】/, '').trim();
      const ph = hint || ('请填写' + displayLbl);
      const div = document.createElement('div');
      div.className = 'fact-field';
      div.innerHTML = `<div class="fact-label">${displayLbl}</div><textarea class="fact-textarea" id="claim-field-${key}" rows="2" placeholder="${esc(ph)}">${esc(val)}</textarea>`;
      container.appendChild(div);
    });
  }
  // claims-full removed in v4 - full text no longer used
  const clmSet = (id, val) => { const el = document.getElementById(id); if (el && val) el.value = val; };
  clmSet('claim-total', c.total);
  clmSet('claim-lawyer-fee', c.lawyerFee);
  clmSet('claim-preservation', c.preservation);
}

function buildFactsSection() {
  const f = state.data.facts || {};
  const container = document.getElementById('facts-fields-container');
  const fields = getFactsFields(state.caseType);

  container.innerHTML = '';
  let lastSection = null;
  fields.forEach(([key, label, hint]) => {
    const val = f[key] || '';
    // 检测section分隔标签 【责任承担】【其他】等
    const sectionMatch = label.match(/^【(.+?)】/);
    const secName = sectionMatch ? sectionMatch[1] : null;
    const displayLabel = label.replace(/^【.+?】/, '').trim();
    const placeholder = hint || ('请填写' + displayLabel);

    // 插入section分隔线
    if (secName && secName !== lastSection) {
      lastSection = secName;
      const sep = document.createElement('div');
      sep.style.cssText = 'grid-column:1/-1;margin:8px 0 4px;padding:6px 12px;background:rgba(202,167,105,0.08);border-left:2px solid rgba(202,167,105,0.4);font-size:11px;color:var(--gold);letter-spacing:0.06em;border-radius:0 4px 4px 0;';
      sep.textContent = secName;
      container.appendChild(sep);
    }

    const div = document.createElement('div');
    div.className = 'fact-field';
    div.innerHTML = `
      <div class="fact-label">${displayLabel}</div>
      <textarea class="fact-textarea" id="fact-${key}" rows="3" placeholder="请填写${label}">${esc(val)}</textarea>
    `;
    container.appendChild(div);
  });
  // Evidence in separate block
  if (f['facts_evidence'] && document.getElementById('evidence-list'))
    document.getElementById('evidence-list').value = f['facts_evidence'];
}

function getClaimFields(typeId) {
  const CLAIMS = {
    lihun: [
      ['claim_01', '1. 解除婚姻关系', '（具体主张）'],
      ['claim_02', '2. 夫妻共同财产', '无财产□ 有财产□\n（1）房屋明细：归属：原告□ / 被告□ / 其他□( );\n（2）汽车明细：归属：原告□ / 被告□ / 其他□( );\n（3）存款明细：归属：原告□ / 被告□ / 其他□( );\n（4）其他（按照上述样式列明）：'],
      ['claim_03', '3. 夫妻共同债务', '无债务□ 有债务□\n（1）债务 1： 承担主体：原告□ / 被告□ / 其他□( );\n（2）债务 2： 承担主体：原告□ / 被告□ / 其他□( );\n……'],
      ['claim_04', '4. 子女直接抚养', '无此问题□ 有此问题□\n子女 1： 归属：原告□ / 被告□\n子女 2： 归属：原告□ / 被告□'],
      ['claim_05', '5. 子女抚养费', '无此问题□ 有此问题□\n抚养费承担主体：原告□ / 被告□ 金额及明细：\n支付方式：'],
      ['claim_06', '6. 探望权', '无此问题□ 有此问题□\n探望权行使主体：原告□ / 被告□ 行使方式：'],
      ['claim_07', '7. 离婚损害赔偿／离婚 经济补偿／离婚经济 帮助', '无此问题□\n离婚损害赔偿□ 金额：\n离婚经济补偿□ 金额：\n离婚经济帮助□ 金额：'],
      ['claim_08', '8. 是否主张诉讼费用', '是□ 否□'],
      ['claim_09', '9. 其他请求', ''],
      ['claim_10', '诉前保全', ''],
      ['claim_11', '是否已经诉前保全', '是□ 保全法院： 保全时间：\n保全案号：\n否□\n（如申请诉讼保全，请另行提交诉讼保全申请及相关材料）'],
    ],
    mjjd: [
      ['claim_01', '1. 本金', '截至 年 月 日止，尚欠本金 元（人民币，下同；如外币\n需特别注明）'],
      ['claim_02', '2. 利息', '截至 年 月 日止，尚欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_03', '3. 是否要求提前还款或 解除合同', '是□ 提前还款（加速到期）□ / 解除合同□\n否□'],
      ['claim_04', '4. 是否主张担保权利', '是□ 内容：\n否□'],
      ['claim_05', '5. 是否主张实现债权的 费用', '是□ 明细：\n否□'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '7. 其他请求', ''],
      ['claim_08', '8. 标的总额', ''],
    ],
    jrjk: [
      ['claim_01', '1. 本金', '截至 年 月 日止，尚欠本金 元（人民币，下同；如外币\n需特别注明）'],
      ['claim_02', '2. 利息（期内利息、复 利、罚息）', '截至 年 月 日止，欠利息 元、期内利息 元、复\n利 元、罚息（违约金） 元；计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_03', '3. 是否要求提前还款或 解除合同', '是□ 提前还款（加速到期）□ / 解除合同□\n否□'],
      ['claim_04', '4. 是否主张担保权利', '是□ 内容：\n否□'],
      ['claim_05', '5. 是否主张实现债权的 费用', '是□ 明细：\n否□'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '7. 其他请求', ''],
      ['claim_08', '8. 标的总额', ''],
    ],
    maimai: [
      ['claim_01', '1. 给付价款（元）', ''],
      ['claim_02', '2. 迟延给付价款的利息（利率、计算方式、截至日期）', ''],
      ['claim_03', '3. 赔偿因违约所受损失', ''],
      ['claim_04', '4. 是否对标的物的瑕疵提出异议（修理/更换/退货/减价）', ''],
      ['claim_05', '5. 要求继续履行或者解除合同', ''],
      ['claim_06', '6. 是否主张担保权利', ''],
      ['claim_07', '7. 是否主张实现债权的费用', ''],
      ['claim_08', '8. 是否主张诉讼费用', ''],
      ['claim_09', '9. 其他请求', ''],
      ['claim_10', '10. 标的总额', ''],
    ],
    ldzy: [
      ['claim_01', '1. 是否主张工资支付', '是□ 否□ 明细：'],
      ['claim_02', '2. 是否主张未签订书面 劳动合同双倍工资', '是□ 否□ 明细：'],
      ['claim_03', '3. 是否主张加班费', '是□ 否□ 明细：'],
      ['claim_04', '4. 是否主张未休年休假 工资', '是□ 否□ 明细：'],
      ['claim_05', '5. 是否主张未依法缴纳 社会保险费造成的经 济损失', '是□ 否□ 明细：'],
      ['claim_06', '6. 是否主张解除劳动合 同经济补偿', '是□ 否□ 明细：'],
      ['claim_07', '7. 是否主张违法解除劳 动合同赔偿金', '是□ 否□ 明细：'],
      ['claim_08', '8. 是否主张诉讼费用', '是□ 否□'],
      ['claim_09', '9. 其他诉讼请求', ''],
      ['claim_10', '10. 标的总额', ''],
      ['claim_11', '诉前保全', ''],
      ['claim_12', '是否已经诉前保全', '是□ 保全法院： 保全时间：\n保全案号：\n否□\n（如申请诉讼保全，请另行提交诉讼保全申请及相关材料）'],
    ],
    jtsg: [
      ['claim_01', '1. 医疗费（金额）', ''],
      ['claim_02', '2. 护理费（金额）', ''],
      ['claim_03', '3. 营养费（金额）', ''],
      ['claim_04', '4. 住院伙食补助费（金额）', ''],
      ['claim_05', '5. 误工费（金额）', ''],
      ['claim_06', '6. 交通费（金额）', ''],
      ['claim_07', '7. 残疾赔偿金（含被扶养人生活费，金额）', ''],
      ['claim_08', '8. 残疾辅助器具费（金额）', ''],
      ['claim_09', '9. 死亡赔偿金、丧葬费（金额）', ''],
      ['claim_10', '10. 精神损害抚慰金（金额）', ''],
      ['claim_11', '11. 财产损失（金额）', ''],
      ['claim_12', '12. 其他费用（项目及金额）', ''],
      ['claim_13', '13. 是否主张诉讼费用', ''],
      ['claim_14', '14. 标的总额', ''],
    ],
    xyk: [
      ['claim_01', '1.透支本金', '截至 年 月 日止，尚欠本金 元（人民币，下同；如为外币需特别注明）；'],
      ['claim_02', '2.利息、罚息、复利、滞纳金、违约金、手续费等', '截至 年 月 日止，欠利息、罚息、复利、滞纳金、违约金、手续费等共计 元\n自 年 月 日之后的利息、罚息、复利、滞纳金、违约金以及手续费等各项费用按照信用卡领用协议计算至实际清偿之日止\n明细：'],
      ['claim_03', '3.是否主张担保权利', '是£ 内容：\n否£'],
      ['claim_04', '4.是否主张实现债权的费用', '是£ 费用明细：\n否£'],
      ['claim_05', '5.是否主张诉讼费用', '是£\n否£'],
      ['claim_06', '6.其他请求', ''],
      ['claim_07', '7.标的总额', ''],
    ],
    wyfw: [
      ['claim_01', '1. 物业费', '截至 年 月 日止，尚欠物业费 元'],
      ['claim_02', '2. 违约金', '截至 年 月 日止，欠逾期物业费的违约金 元\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_03', '3. 是否主张诉讼费用', '是□ 否□'],
      ['claim_04', '4. 其他请求', ''],
      ['claim_05', '5. 标的总额', ''],
    ],
    bxcss: [
      ['claim_01', '1. 理赔款', '支付理赔款 元（人民币，下同；如外币需特别注明）\n费用明细：'],
      ['claim_02', '2. 是否主张实现债权的 费用', '是□ 费用明细：\n否□'],
      ['claim_03', '3. 是否主张诉讼费用', '是□ 否□'],
      ['claim_04', '4. 其他请求', ''],
      ['claim_05', '5. 标的总额', ''],
    ],
    zqxjcs: [
      ['claim_01', '1. 赔偿因虚假陈述导致 的损失', '投资差额损失 元、佣金损失 元、印花税损失 元\n（人民币，下同；如外币需特别注明）'],
      ['claim_02', '2. 是否主张连带责任', '是□ 责任主体及责任范围：\n否□'],
      ['claim_03', '3. 是否主张实现债权的 费用', '是□ 费用明细：\n否□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', ''],
      ['claim_06', '6. 标的总额', ''],
    ],
    bzxbx: [
      ['claim_01', '1. 理赔款', '支付理赔款 元（人民币，下同；如外币需特别注明）'],
      ['claim_02', '2. 保险费、违约金等', '截至 年 月 日止，欠保险费、违约金等共计 元\n自 年 月 日之后的保险费、违约金等各项费用按照保证保险合\n同约定计算至实际清偿之日止 明细：'],
      ['claim_03', '3. 是否主张实现债权的 费用', '是□ 费用明细：\n否□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', ''],
      ['claim_06', '6. 标的总额', ''],
    ],
    rongzi: [
      ['claim_01', '1. 支付全部未付租金（金额）', ''],
      ['claim_02', '2. 违约金、滞纳金、损失赔偿（金额）', ''],
      ['claim_03', '3. 是否确认租赁物归原告所有', ''],
      ['claim_04', '4. 请求解除合同', ''],
      ['claim_05', '5. 返还租赁物，并赔偿因解除合同受到的损失', ''],
      ['claim_06', '6. 是否主张担保权利', ''],
      ['claim_07', '7. 是否主张实现债权的费用', ''],
      ['claim_08', '8. 是否主张诉讼费用', ''],
      ['claim_09', '9. 其他请求', ''],
      ['claim_10', '10. 标的总额', ''],
    ],
    fwmm: [
      ['claim_01', '1. 确定房屋买卖合同 关系', '无此问题□ 有此问题□\n主张确认合同无效□ 主张确认合同未成立□ 主张解除□ 主张撤销□ 主张继续履行□\n主张订立正式房屋买卖合同□\n具体主张： （例：确认合同无效 / 继续履行 / 解除合同 / 撤销 合同 / 否定某约定合同效力 / 要求订立本约）'],
      ['claim_02', '2. 支付或返还购房款', '无此问题□ 有此问题□\n具体主张：主张返还首付款□ / 定金□ / 已付款□ 主张支付欠付房款□\n主张支付违约金□或利息□\n主张赔偿损失□ 金额及明细：'],
      ['claim_03', '3. 交付或返还房屋', '无此问题□ 有此问题□\n主张交付房屋：是□ / 否□ 主张返还房屋：是□ / 否□\n主张支付逾期交房违约金：是□ / 否□'],
      ['claim_04', '4. 办理房屋登记手续', '无此问题□ 有此问题□\n主张协助办理不动产登记：是□ / 否□ 主张支付逾期办证违约金：是□ / 否□'],
      ['claim_05', '5. 返还或承担中介服 务费', '无此问题□ 有此问题□\n主张返还中介服务费：是□ / 否□\n主张被告承担中介服务费：是□ / 否□ 金额及明细：'],
      ['claim_06', '6. 房屋质量损害赔偿', '无此问题□ 有此问题□\n主张被告予以维修：是□ / 否□\n主张被告承担原告垫付的维修费：是□ / 否□ 金额及明细：'],
      ['claim_07', '7. 解除担保贷款（按揭） 合同', '无此问题□\n有此问题□ 具体要求：'],
      ['claim_08', '8. 鉴定及其他实现债权 的费用', '无此问题□ 有此问题□\n请求委托鉴定：是□ / 否□ 费用明细：'],
      ['claim_09', '9. 是否主张诉讼费用', '是□ 否□'],
      ['claim_10', '10. 其他请求', ''],
      ['claim_11', '11. 标的总额', ''],
    ],
    fwzl: [
      ['claim_01', '1. 支付租金（截至日期及欠付金额）', ''],
      ['claim_02', '2. 迟延支付租金的利息', ''],
      ['claim_03', '3. 交付房屋', ''],
      ['claim_04', '4. 请求解除合同', ''],
      ['claim_05', '5. 返还租赁物，并赔偿因解除合同受到的损失', ''],
      ['claim_06', '6. 支付房屋占有使用费（金额）', ''],
      ['claim_07', '7. 支付水电费等费用（金额）', ''],
      ['claim_08', '8. 返还押金（金额）', ''],
      ['claim_09', '9. 是否主张实现债权的费用', ''],
      ['claim_10', '10. 是否主张诉讼费用', ''],
      ['claim_11', '11. 其他请求', ''],
      ['claim_12', '12. 标的总额', ''],
    ],
    jsgc: [
      ['claim_01', '1. 支付工程款（金额）', ''],
      ['claim_02', '2. 迟延支付工程款的利息', ''],
      ['claim_03', '3. 是否主张建设工程价款优先受偿权', ''],
      ['claim_04', '4. 是否请求与原告没有合同关系的发包人承担责任', ''],
      ['claim_05', '5. 是否要求赔偿损失（金额）', ''],
      ['claim_06', '6. 是否退还超付的工程款', ''],
      ['claim_07', '7. 是否支付超付工程款利息', ''],
      ['claim_08', '8. 是否对建设工程承担修复责任', ''],
      ['claim_09', '9. 请求确认建设工程施工合同无效', ''],
      ['claim_10', '10. 要求继续履行或是解除合同', ''],
      ['claim_11', '11. 是否主张实现债权的费用', ''],
      ['claim_12', '12. 是否主张诉讼费用', ''],
      ['claim_13', '13. 其他请求', ''],
      ['claim_14', '14. 标的总额', ''],
    ],
    rsbx: [
      ['claim_01', '1. 保险金', '支付保险金 元（人民币，下同；如外币需特别注明）\n费用明细：\n□生存保险金 元 □重大疾病保险金 元\n□身故保险金 元 □医疗费保险金 元\n□伤残保险金 元 □红利、收益元 □其他 元\n其中，保险金以实际发生的人身损害为计算依据，赔偿项目包括：\n□医疗费 元\n年 月 日至 年 月 日期间在医院住院（门诊）治疗，\n累计发生医疗费 元\n医疗费发票、医疗费清单、病历资料：有□ 无□\n□护理费 元\n住院护理 天支付护理费 元（或护理人员发生误工费\n元），或遵医嘱短期护理发生护理费 元\n住院证明、医嘱等：有□ 无□\n□营养费 元\n病历资料：有□ 无□\n□住院伙食补助费 元 病历资料：有□ 无□\n□误工费 元\n年 月 日至 年 月 日误工费 元\n□交通费 元\n交通费凭证：有□ 无□ □伤残鉴定费 元\n经鉴定，构成伤残 级，鉴定费 元；\n□残疾辅助器具费 元 □其他 元'],
      ['claim_02', '2. 保单现金价值', '元\n返还情形：□合同解除 □拒赔 □其他'],
      ['claim_03', '3. 保险费', '元'],
      ['claim_04', '4. 是否主张实现债权的 费用', '是□ 费用明细：\n否□'],
      ['claim_05', '5. 是否主张诉讼费用', '是□ 否□'],
      ['claim_06', '6. 其他请求', ''],
      ['claim_07', '7. 标的总额', ''],
    ],
    zebx: [
      ['claim_01', '1. 理赔款', '支付理赔款 元（人民币，下同；如外币需特别注明）\n费用明细：\n（1）因事故导致的人身损害赔偿项目，包括：\n□医疗费 元\n年 月 日至 年 月 日期间在医院住院（门诊）治疗，\n累计发生医疗费 元\n医疗费发票、医疗费清单、病历资料：有□ 无□\n□护理费 元\n住院护理天支付护理费 元（或护理人员发生误工费元），或遵医嘱短期护理 发生护理费 元\n住院证明、医嘱等：有□ 无□\n□营养费 元\n病历资料：有□ 无□\n□住院伙食补助费 元 病历资料：有□ 无□\n□误工费 元\n从 事 工 作， 收 入 状 况 ， 误 工 时 间 自 年 月\n日计至年月日，共 天，误工费 元\n□交通费 元\n交通费凭证：有□ 无□ □伤残鉴定费 元\n经鉴定，构成伤残级，鉴定费 元；\n□残疾辅助器具费 元 □其他 元\n（2）因事故导致的非人身相关的财产损失，包括：'],
      ['claim_02', '2. 是否主张实现债权的 费用', '是□ 费用明细：\n否□'],
      ['claim_03', '3. 是否主张诉讼费用', '是□ 否□'],
      ['claim_04', '4. 其他请求', ''],
      ['claim_05', '5. 标的总额', ''],
    ],
    xzcf: [
      ['claim_01', '1. □撤销行政处罚行为', ''],
      ['claim_02', '2. □确认行政处罚行为违法', ''],
      ['claim_03', '3. □确认行政处罚行为无效', ''],
      ['claim_04', '4. □变更行政处罚行为', '变更为：'],
      ['claim_05', '5. □责令被告采取补救 措施', '补救措施的具体内容：'],
      ['claim_06', '6. □被告承担赔偿责任', '具体赔偿请求： 依据：'],
      ['claim_07', '7. 是否主张诉讼费用', '□是 □否'],
      ['claim_08', '8. □其他请求', ''],
    ],
    xzqzzx: [
      ['claim_01', '1. □撤销行政强制执行决定', ''],
      ['claim_02', '2. □确认行政强制执行行为违法', ''],
      ['claim_03', '3. □确认行政强制执行行为无效', ''],
      ['claim_04', '4. □责令被告采取补救 措施', '补救措施的具体内容：'],
      ['claim_05', '5. □被告承担赔偿责任', '具体赔偿请求： 依据：'],
      ['claim_06', '6. 是否主张诉讼费用', '□是 □否'],
      ['claim_07', '7. □其他请求', ''],
    ],
    xzxk: [
      ['claim_01', '1. □撤销行政许可行为', '说明：此处行政许可行为包含准予许可、不予许可，变更、延续、撤回、 注销、撤销许可等行为。\n具体内容：'],
      ['claim_02', '2. □确认行政许可行为 违法', '说明：此处行政许可行为包含准予许可、不予许可，变更、延续、撤回、 注销、撤销许可等行为。\n具体内容：'],
      ['claim_03', '3. □确认行政许可行为 无效', '说明：此处行政许可行为包含准予许可、不予许可，变更、延续、撤回、 注销、撤销许可等行为。\n具体内容：'],
      ['claim_04', '4. □变更行政许可行为', '说明：此处行政许可行为包含准予许可、不予许可，变更、延续、撤回、 注销、撤销许可等行为。\n具体内容：'],
      ['claim_05', '5. □责令被告采取补救 措施', '补救措施的具体内容：'],
      ['claim_06', '6. □被告承担赔偿责任', '具体赔偿请求： 依据：'],
      ['claim_07', '7. 是否主张诉讼费用', '□是 □否'],
      ['claim_08', '8. □其他请求', ''],
    ],
    fwzs: [
      ['claim_01', '1. □撤销国有土地上房屋征收决定', ''],
      ['claim_02', '2. □确认国有土地上房屋征收决定违法', ''],
      ['claim_03', '3. □确认国有土地上房屋征收决定无效', ''],
      ['claim_04', '4. 是否主张诉讼费用', '□是 □否'],
      ['claim_05', '5. □其他请求', ''],
    ],
    gsbx: [
      ['claim_01', '1. □撤销认定工伤决定', ''],
      ['claim_02', '2. □撤销不予认定工伤 决定', ''],
      ['claim_03', '3. 是否主张诉讼费用', '□是 □否'],
      ['claim_04', '4. □其他请求', ''],
    ],
    zfxxgk: [
      ['claim_01', '1. □要求被告在一定期限内答复', ''],
      ['claim_02', '2. □撤销政府信息公开答复', ''],
      ['claim_03', '3. □要求确认被告公开 / 不公开政府信息的行为违法', ''],
      ['claim_04', '4. □要求行政机关提供与申请内容相一致的政府信息', ''],
      ['claim_05', '5. □要求行政机关按照其要求的形式提供政府信息', ''],
      ['claim_06', '6. 是否主张诉讼费用', '□是 □否'],
      ['claim_07', '7. □其他请求', ''],
    ],
    xzfy: [
      ['claim_01', '1. □撤销行政复议决定', ''],
      ['claim_02', '2. □确认行政复议决定违法', ''],
      ['claim_03', '3. □确认行政复议决定无效', ''],
      ['claim_04', '4. 是否主张诉讼费用', '□是 □否'],
      ['claim_05', '5. □其他请求', ''],
    ],
    xzxy: [
      ['claim_01', '1. □确认行政协议无效', ''],
      ['claim_02', '2. □撤销行政协议', ''],
      ['claim_03', '3. □要求继续履行协议 约定的内容', '要求履行内容：'],
      ['claim_04', '4. □变更行政协议', '变更为：'],
      ['claim_05', '5. □解除行政协议', ''],
      ['claim_06', '6. □责令被告采取补救 措施', '补救措施的具体内容：'],
      ['claim_07', '7. □请求被告支付违约 金或承担其他违约责任', '具体内容：'],
      ['claim_08', '8. □被告对给原告造成 的损失承担赔偿责任', '具体赔偿请求： 依据：'],
      ['claim_09', '9. 是否主张诉讼费用', '□是 □否'],
      ['claim_10', '10. □其他请求', ''],
    ],
    xzbc: [
      ['claim_01', '1. □房屋征收或者征用 补偿', '□撤销或者变更补偿决定\n□确认补偿决定违法\n□确认补偿决定无效\n□行政机关予以补偿 具体内容：'],
      ['claim_02', '2. □土地征收或者征用 补偿', '□撤销或者变更补偿决定\n□确认补偿决定违法\n□确认补偿决定无效\n□行政机关予以补偿 具体内容：'],
      ['claim_03', '3. □动产征收或者征用 补偿', '□撤销或者变更补偿决定\n□确认补偿决定违法\n□确认补偿决定无效\n□行政机关予以补偿 具体内容：'],
      ['claim_04', '4. □撤回行政许可补偿', '□撤销或者变更补偿决定\n□确认补偿决定违法\n□确认补偿决定无效\n□行政机关予以补偿 具体内容：'],
      ['claim_05', '5. □收回国有土地使用 权补偿', '□撤销或者变更补偿决定\n□确认补偿决定违法\n□确认补偿决定无效\n□行政机关予以补偿 具体内容：'],
      ['claim_06', '6. □规划变更补偿', '□撤销或者变更补偿决定\n□确认补偿决定违法\n□确认补偿决定无效\n□行政机关予以补偿 具体内容：'],
      ['claim_07', '7. 是否主张诉讼费用', '□是 □否'],
      ['claim_08', '8. □其他请求', ''],
    ],
    xzpc: [
      ['claim_01', '1. □要求行政机关予以 赔偿', '具体内容：'],
      ['claim_02', '2. □确认行政行为违法 并赔偿', '具体内容：'],
      ['claim_03', '3. □撤销或者变更赔偿 决定', '具体内容：'],
      ['claim_04', '4. □其他请求', ''],
    ],
    xzbllzz: [
      ['claim_01', '1. □确认不履行法定职 责行为违法', '具体内容：'],
      ['claim_02', '2. □要求行政机关履行 法定职责', '具体内容：'],
      ['claim_03', '3. 是否主张诉讼费用', '□是 □否'],
      ['claim_04', '4. □其他请求', ''],
    ],
    xswrw: [
      ['claim_01', '1. 请求对被告人 ××× 以侮辱罪追究刑事责任。 2.（提起附带民事诉讼的）请求被告人 ××× 赔偿因犯罪行为给自诉人造成的物质损失。 3.（其他请求）。 通过信息网络实施侮辱行为，自诉人提供证据确有困难的，是否需要公安机关提供协助 是□（具体事项和线索） 否□', ''],
    ],
    xsfb: [
      ['claim_01', '1. 请求对被告人 ××× 以诽谤罪追究刑事责任。 2.（提起附带民事诉讼的）请求被告人 ××× 赔偿因犯罪行为给自诉人造成的物质损失。 3.（其他请求）。 通过信息网络实施诽谤行为，自诉人提供证据确有困难的，是否需要公安机关提供协助 是□ （具体事项和线索） 否□', ''],
    ],
    xschh: [
      ['claim_01', '1. 请求对被告人 ××× 以重婚罪追究刑事责任。 2.（提起附带民事诉讼的）请求被告人 ××× 赔偿因犯罪行为给自诉人造成的物质损失。 3.（其他请求）', ''],
    ],
    xsjbzx: [
      ['claim_01', '1. 请求对被告人 ××× 以拒不执行判决、裁定罪追究刑事责任。 2.（提起附带民事诉讼的）请求被告人 ××× 赔偿因犯罪行为给自诉人造成的物质损失。 3.（其他请求）', ''],
    ],
    shangbiao: [
      ['claim_01', '1. 停止侵权', '有□\n□ 1. 立 即 停 止 生 产 / 销 售 / 生 产、 销 售 侵 害 原 告 第 号 “ ”商标权的侵权商品\n□ 2. 立即停止在店铺招牌□ 店内装饰□ 宣传册□ 网站（网店） 宣传、链接□ 其他场合□( )使用侵害原告第 号 “ ”商标权的“ ”标识\n□ 3. 立即停止其他侵权行为 无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失 元\n原告损失□ 被告获利□ 商标许可使用费□ 倍数：\n法定赔偿□\n惩罚性赔偿□ 基数的确定方式：原告损失□ 被告获利□\n商标许可使用费□ 倍数： 计算依据或参考因素：\n无□'],
      ['claim_03', '3. 支付合理费用', '有□ 律师费 元 律师费凭证：有□ 无□\n公证费 元 公证费凭证：有□ 无□\n购买产品费 元 购买产品费凭证：有□ 无□\n差旅费 元 差旅费凭证：有□ 无□\n其他费用\n无□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', '有□ 内容：如是否主张连带赔偿责任、赔礼道歉、消除影响等其他请求\n无□'],
    ],
    fmzl: [
      ['claim_01', '1. 停止侵害', '有□ 内容：（具体写明要求停止的侵权行为，如制造、销售、许诺销售等）\n无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失 元\n是否包含惩罚性赔偿：包含□ 计算方法：基数 元 ×（1+ 惩罚性赔\n偿倍数） 不包含□\n无□'],
      ['claim_03', '3. 赔偿维权合理开支', '有□ 律师费 元 凭证：有□ 无□\n公证费 元 凭证：有□ 无□\n差旅费 元 凭证：有□ 无□\n其他费用 元 凭证：有□ 无□ 无□'],
      ['claim_04', '4. 连带责任', '有□ 内容：\n无□'],
      ['claim_05', '5. 非金钱给付义务迟延 履行金', '有□ 内容：\n无□'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '7. 其他请求', '有□ 内容：\n无□'],
    ],
    wgsj: [
      ['claim_01', '1. 停止侵权', '有□ 内容：具体陈述侵权对象、停止侵权的方式和内容等，如停止制造、 销售、许诺销售等\n无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失共计 元\n原告损失□ 元；被告获利□ 元；许可使用费□ 元（基\n数： 元，倍数： 倍）； 计算依据或参考因素：\n惩罚性赔偿□ 元（基数： 元，倍数： 倍）；\n计算依据或参考因素：\n无□'],
      ['claim_03', '3. 支付合理费用', '有□ 律师费 元 律师费凭证：有□ 无□\n公证费 元 公证费凭证：有□ 无□\n差旅费 元 差旅费凭证：有□ 无□\n其他费用 元 凭证：有□ 无□\n无□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', '有□ 内容：\n无□'],
      ['claim_06', '诉前保全', ''],
      ['claim_07', '是否已经诉前保全', '是□ 保全法院： 保全时间：\n保全案号：\n否□\n（如申请诉讼保全，请另行提交诉讼保全申请及相关材料）'],
    ],
    zwxpz: [
      ['claim_01', '1. 停止侵害', '有□ 内容：（简述停止侵权主体以及相应停止侵权方式、内容、范围等）\n无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失 元\n是否包含惩罚性赔偿：包含□, 计算方法：基数 元 ×（1+ 惩罚性 赔偿倍数 ）\n不包含□\n无□'],
      ['claim_03', '3. 赔偿维权合理开支', '有□ 律师费 元 凭证：有□ 无□\n公证费 元 凭证：有□ 无□\n差旅费 元 凭证：有□ 无□\n其他费用 元 凭证：有□ 无□\n无□'],
      ['claim_04', '4. 连带责任', '有□ 内容：\n无□'],
      ['claim_05', '5. 非金钱给付义务迟延 履行金', '有□ 内容：\n无□'],
      ['claim_06', '6. 是否主张诉讼费用', '有□ 内容：\n无□'],
      ['claim_07', '7. 其他请求', '有□ 内容：\n无□'],
    ],
    zhuzuoquan: [
      ['claim_01', '1. 停止侵权', '□立即停止使用与原告作品 （作品名称 / 登记证号） 相同 / 实质性相似的作品：\n侵权链接 / 标题：'],
      ['claim_02', '2. 赔偿经济损失', '经济损失 元\n原告损失□ 被告获利□ 许可费用□ 法定赔偿□\n惩罚性赔偿□ 基数□ 倍数□\n计算依据或参考因素：'],
      ['claim_03', '3. 支付合理费用', '有□ 律师费 元 律师费凭证：有□ 无□\n取证费 元 取证费凭证：有□ 无□\n差旅费 元 差旅费凭证：有□ 无□\n其他\n无□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', '如是否主张连带赔偿责任、赔礼道歉、消除影响等其他请求'],
    ],
    jishu: [
      ['claim_01', '1. 要求继续履行或是解 除合同', '继续履行□ 日内履行完毕 判令解除合同□\n确认合同已于 年 月 日解除'],
      ['claim_02', '2. 给付价款', '元（人民币，下同；如外币需特别注明）'],
      ['claim_03', '3. 迟延给付价款、报酬 及使用费的利息（违 约金）', '有□ 截至 年 月 日止，迟延给付价款的利息 元；违\n约 金 元； 自 之 后 的逾 期 利 息、 违 约 金， 以 元 为 基 数 按\n照 标准计算：\n计算方式：\n无□'],
      ['claim_04', '4. 赔偿违约所受的损失', '有□ 支付赔偿金 元\n违约类型：迟延履行□ 不履行□ 其他□\n具体情形：\n损失计算依据： 无□'],
      ['claim_05', '5. 是否主张诉讼费用', '是□ 否□'],
      ['claim_06', '6. 其他请求', '有□ 内容：如是否主张连带赔偿责任等其他请求\n无□'],
      ['claim_07', '鉴定和诉前保全', ''],
      ['claim_08', '1. 是否申请鉴定', '是□ 鉴定内容：\n鉴定机构名称：\n否□'],
      ['claim_09', '2. 是否已经诉前保全', '是□ 保全法院： 保全时间：\n保全案号：\n否□\n（如申请诉讼保全，请另行提交诉讼保全申请及相关材料）'],
    ],
    bzdj: [
      ['claim_01', '1. 停止侵害', '有□ 内容：具体陈述侵害对象、停止侵权的方式和内容等\n无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失共计 元\n原告损失□ 元；被告获利☑ 元；法定赔偿□ 元；\n计算依据或参考因素：\n具体计算方式（选择以原告损失或被告获利计算赔偿数额时）：\n无□'],
      ['claim_03', '3. 支付合理费用', '有□ 律师费 元 律师费凭证：有□ 无□\n公证费 元 公证费凭证：有□ 无□\n差旅费 元 差旅费凭证：有□ 无□\n其他费用 元 凭证：有□ 无□ 无□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 消除影响', '有□ 无□'],
      ['claim_06', '6. 其他请求', ''],
    ],
    longduan: [
      ['claim_01', '1. 停止垄断行为', '有□ 内容：（简述请求停止的垄断行为内容）\n无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失 元\n无□'],
      ['claim_03', '3. 赔偿维权合理开支', '有□ 律师费 元 凭证：有□ 无□\n经济分析费 元 凭证：有□ 无□\n市场调查费 元 凭证：有□ 无□\n其他费用 元 凭证：有□ 无□\n无□'],
      ['claim_04', '4. 连带责任', '有□ 内容：\n无□'],
      ['claim_05', '5. 非金钱给付义务迟延 履行金', '有□ 内容：\n无□'],
      ['claim_06', '6. 是否主张诉讼费用', '有□ 内容：\n无□'],
      ['claim_07', '7. 其他请求', '有□ 内容：\n无□'],
    ],
    syms: [
      ['claim_01', '1. 停止侵权', '有□ 内容：具体陈述侵权对象、停止侵权的方式和内容等。\n无□'],
      ['claim_02', '2. 赔偿经济损失', '有□ 经济损失共计 元\n原告损失□ 元；被告获利□ 元；法定赔偿□ 元；\n计算依据或参考因素：\n惩罚性赔偿□ 倍数： 倍\n计算依据或参考因素：\n无□'],
      ['claim_03', '3. 支付合理费用', '有□ 律师费 元 律师费凭证：有□ 无□\n公证费 元 公证费凭证：有□ 无□\n差旅费 元 差旅费凭证：有□ 无□\n其他费用 元 凭证：有□ 无□ 无□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', '有□ 无□'],
    ],
    sbsqbhfs: [
      ['claim_01', '1. 被诉决定', '商评字［202 ］第 号关于第 号 商标驳回复审决定'],
      ['claim_02', '2. 被诉决定作出时间', '年 月 日'],
      ['claim_03', '3. 争议法条', ''],
    ],
    sbcxfs: [
      ['claim_01', '（请概况描述诉讼请求，相关具体内容请在下方要素式表格中填写）', ''],
      ['claim_02', '1. 诉讼请求', '□主张撤销被诉决定。\n□判令被告重新作出复审决定。 □其他：'],
      ['claim_03', '2. 是否主张诉讼费用', '是□ 否□'],
      ['claim_04', '3. 其他请求', '有□ 内容：\n无□'],
    ],
    sbwx: [
      ['claim_01', '（请概况描述诉讼请求事项，相关具体内容请在下方要素式表格中填写）', ''],
      ['claim_02', '1. 诉讼请求', '□主张撤销被诉决定。\n□判令被告重新作出复审决定。 □其他：'],
      ['claim_03', '2. 是否主张诉讼费用', '是□ 否□'],
    ],
    zlbhfs: [
      ['claim_01', '1. 关于被诉决定', '判决撤销国家知识产权局第 ×× 号复审请求审查决定（以下简称“被诉决 定”），判令被告重新作出审查决定。'],
      ['claim_02', '2. 是否主张诉讼费用', '是□ 否□'],
    ],
    zlwx: [
      ['claim_01', '1. 关于被诉决定', '判决撤销国家知识产权局第 ×× 号无效宣告请求审查决定（以下简称“被 诉决定”），判令被告重新作出审查决定。'],
      ['claim_02', '2. 是否主张诉讼费用', '是□ 否□'],
    ],
    ldzxz: [
      ['claim_01', '1. 关于被诉决定', '判决撤销 ×× 市场监督管理局 ×× 号行政处罚决定书（以下简称“被诉 决定”）。'],
      ['claim_02', '2. 是否主张诉讼费用', '是□ 否□'],
    ],
    hjwr: [
      ['claim_01', '1. 侵权责任', '□停止侵害\n□排除妨碍\n□消除危险\n□修复生态环境\n□赔偿损失\n□赔礼道歉'],
      ['claim_02', '2. 修复生态环境', '□清除污染费用数额： 元\n□修复生态环境费用数额： 元\n□防止损害的发生和扩大所支出的合理费用： 元\n以上共计 元（人民币，下同；如外币需特别注明）。'],
      ['claim_03', '3. 赔偿损失', '□生态环境受到损害至修复完成期间服务功能丧失导致的损失： 元\n□生态环境功能永久性损害造成的损失： 元\n□生态环境损害调查、鉴定评估等费用： 元\n□其他费用： 元 以上共计 元。'],
      ['claim_04', '4. 其他请求', ''],
      ['claim_05', '5. 总额', '以上共计 元。'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '生态环境侵权禁止令保全措施', ''],
      ['claim_08', '1. 是否已经申请诉前生 态环境侵权禁止令保 全措施', '是□ 保全法院： 保全时间：\n保全案号：\n否□'],
      ['claim_09', '2. 是否申请生态环境侵 权禁止令保全措施', '是□ （请另行提交保全申请及相关材料）\n否□'],
    ],
    stph: [
      ['claim_01', '1. 侵权责任', '□停止侵害\n□排除妨碍\n□消除危险\n□修复生态环境\n□赔偿损失\n□赔礼道歉'],
      ['claim_02', '2. 修复生态环境', '□清除污染费用数额： 元\n□修复生态环境费用数额： 元\n□防止损害的发生和扩大所支出的合理费用： 元\n以上共计 元（人民币，下同；如外币需特别注明）。'],
      ['claim_03', '3. 赔偿损失', '□生态环境受到损害至修复完成期间服务功能丧失导致的损失： 元\n□生态环境功能永久性损害造成的损失： 元\n□生态环境损害调查、鉴定评估等费用： 元\n□其他费用： 元\n以上共计 元。'],
      ['claim_04', '4. 其他请求', ''],
      ['claim_05', '5. 总额', '以上共计 元。'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '生态环境侵权禁止令保全措施', ''],
      ['claim_08', '1. 是否已经申请诉前生 态环境侵权禁止令保 全措施', '是□ 保全法院： 保全时间：\n保全案号：\n否□'],
      ['claim_09', '2. 是否申请生态环境侵 权禁止令保全措施', '是□ （请另行提交保全申请及相关材料）\n否□'],
    ],
    stsh: [
      ['claim_01', '1. 侵权责任', '□停止侵害\n□排除妨碍\n□消除危险\n□修复生态环境\n□赔偿损失\n□赔礼道歉'],
      ['claim_02', '2. 修复生态环境', '□清除污染费用数额： 元\n□修复生态环境费用数额： 元\n□防止损害的发生和扩大所支出的合理费用数额： 元 以上共计 元（人民币，下同；如外币需特别注明）。'],
      ['claim_03', '3. 赔偿损失', '□生态环境受到损害至修复完成期间服务功能丧失导致的损失数额： 元\n□生态环境功能永久性损害造成的损失数额： 元\n□生态环境损害调查、鉴定评估等费用数额： 元\n□其他费用数额： 元 以上共计 元。'],
      ['claim_04', '4. 其他请求', ''],
      ['claim_05', '5. 总额', '以上共计 元。'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '生态环境侵权禁止令保全措施', ''],
      ['claim_08', '1. 是否已经申请诉前生 态环境侵权禁止令保 全措施', '是□ 保全法院： 保全时间：\n保全案号：\n否□'],
      ['claim_09', '2. 是否申请生态环境侵 权禁止令保全措施', '是□ （请另行提交保全申请及相关材料）\n否□'],
    ],
    cbpz: [
      ['claim_01', '1. 是否主张船舶价值损 失（含修理费等）及 利息', '是□ 否□\n损失项目及金额： 元（人民币，下同；如外币需特别注明）截至 年\n月 日止，欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_02', '2. 是否主张船上财产损 失（船载货物、渔船 捕捞设备、网具）及 利息', '是□ 否□\n损失项目及金额： 截至 年 月 日止，欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_03', '3. 是否主张救助费、沉 船打捞清除费、拖航 费、共同海损分摊等 及利息', '是□ 否□\n损失项目及金额： 截至 年 月 日止，欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_04', '4. 是否主张本航次租金 或运费损失、船期损 失及利息', '是□ 否□\n损失项目及金额： 截至 年 月 日止，欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_05', '5. 是否主张船上人身伤 亡损失及利息', '是□ 否□\n损失项目及金额： 截至 年 月 日止，欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '7. 其他损失', '项目：\n费用： 元'],
      ['claim_08', '8. 标的总额', '元（暂计至 年 月 日）'],
    ],
    hsrs: [
      ['claim_01', '1. 医疗费', '年 月 日至 年 月 日期间在 医院住院（门诊）\n治疗，累计支付医疗费 元\n医疗费发票、医疗费清单、病历资料：有□ 无□'],
      ['claim_02', '2. 护理费', '住院护理 天支付护理费 元（或护理人员发生误工费 元），或遵医\n嘱短期护理发生护理费 元\n住院证明、医嘱等：有□ 无□'],
      ['claim_03', '3. 营养费', '营养费 元\n病历资料：有□ 无□'],
      ['claim_04', '4. 住院伙食补助费', '住院伙食补助费 病历资料：有□'],
      ['claim_05', '5. 误工费', '年 月 日至 年 月 日误工费 元'],
      ['claim_06', '6. 交通费', '交通费 元\n交通费凭证：有□ 无□'],
      ['claim_07', '7. 残疾赔偿金（被扶养 人生活费计入）', '残疾赔偿金 元（含被扶养人生活费 元）'],
      ['claim_08', '8. 残疾辅助器具费', '残疾辅助器具费 元'],
      ['claim_09', '9. 死亡赔偿金（被扶养 人生活费计入）、丧葬费', '死亡赔偿金 元（含被扶养人生活费 元），丧葬费 元'],
      ['claim_10', '10. 精神损害抚慰金', '精神损害抚慰金 元'],
      ['claim_11', '11. 是否主张诉讼费用', '是□ 否□'],
      ['claim_12', '12. 其他费用', '主张 费用 元'],
      ['claim_13', '13. 赔偿总额', '元（计至 年 月 日）'],
      ['claim_14', '14. 是否主张船舶优先权', '是□ 内容：\n否□'],
    ],
    hshyd: [
      ['claim_01', '1. 费用类型及金额', ''],
      ['claim_02', '2. 是否主张逾期付款利 息损失', '是□ 费用本金： 截至 年 月 日止，欠利息 元；\n计算方式：\n是否请求支付至实际清偿之日止：是□ 否□\n否□'],
      ['claim_03', '3. 是否主张实现债权的 费用', '是□ 费用明细：\n否□'],
      ['claim_04', '4. 是否主张诉讼费用', '是□ 否□'],
      ['claim_05', '5. 其他请求', '是□ 内容：\n否□'],
      ['claim_06', '6. 标的总额', '元（暂计至 年 月 日）'],
    ],
    cylw: [
      ['claim_01', '1. 船员工资', '有□ 年 月 日至 年 月\n计拖欠船员工资 元 欠条：有□\n无□'],
      ['claim_02', '2. 遣返费用', '有□ 交通费 元，住宿费 元，其他 元\n无□'],
      ['claim_03', '3. 其他报酬或费用', '有□ 项目： 金额： 元\n无□'],
      ['claim_04', '4. 费用总额', '元'],
      ['claim_05', '5. 是否主张船舶优先权', '是□ 内容：请求确认原告的诉讼请求（ 元）对“×××”船享有船舶优先权，有权在船舶拍卖、变卖款中优先受偿。\n否□'],
      ['claim_06', '6. 是否主张诉讼费用', '是□ 否□'],
      ['claim_07', '7. 本表未列明的其他 请求', ''],
    ],
    zxyysqs: [
      ['claim_01', '1. 异议事项类型（执行标的/标的额/查扣冻财产/财产处置/结案等）', ''],
      ['claim_02', '2. 异议请求', ''],
      ['claim_03', '3. 事实与理由', ''],
      ['claim_04', '4. 证据清单', ''],
    ],
    zxfysqs: [
      ['claim_01', '1. 复议事项类型（执行标的/标的额/查扣冻财产/惩戒措施/结案等）', ''],
      ['claim_02', '2. 原文书号及送达日期', ''],
      ['claim_03', '3. 复议请求', ''],
      ['claim_04', '4. 事实与理由', ''],
      ['claim_05', '5. 证据清单', ''],
    ],
    zxjdsqs: [
      ['claim_01', '1. 监督事项类型（执行标的/标的额/查扣冻财产/惩戒措施/结案等）', ''],
      ['claim_02', '2. 原文书号及送达日期', ''],
      ['claim_03', '3. 监督请求', ''],
      ['claim_04', '4. 事实与理由', ''],
      ['claim_05', '5. 证据清单', ''],
    ],
    byyxzc: [
      ['claim_01', '1. 不予执行文书类型（仲裁裁决/调解书/公证债权文书）', ''],
      ['claim_02', '2. 文书作出机构及文书号', ''],
      ['claim_03', '3. 执行案号及执行通知书送达日期', ''],
      ['claim_04', '4. 申请不予执行类型（对应法定事由）', ''],
      ['claim_05', '5. 申请请求', ''],
      ['claim_06', '6. 事实与理由', ''],
      ['claim_07', '7. 证据清单', ''],
    ],
    gjpcsqs1: [['claim_01', '1. 申请赔偿的法律依据和理由', ''],['claim_02', '2. 赔偿请求内容及金额', '']],
    gjpcsqs2: [['claim_01', '1. 申请赔偿的法律依据和理由', ''],['claim_02', '2. 赔偿请求内容及金额', '']],
    gjpcsqs3: [['claim_01', '1. 申请赔偿的法律依据和理由', ''],['claim_02', '2. 赔偿请求内容及金额', '']],
    gjpcsqs4: [['claim_01', '1. 申请赔偿的法律依据和理由', ''],['claim_02', '2. 赔偿请求内容及金额', '']],
  };
  return CLAIMS[typeId] || [
    ['claim_01', '1. 主要诉讼请求（请求内容及金额）', ''],
    ['claim_02', '2. 违约金/赔偿金（如有）', ''],
    ['claim_03', '3. 利息（如有）', ''],
    ['claim_04', '4. 是否主张实现债权的费用', ''],
    ['claim_05', '5. 是否主张诉讼费用', ''],
    ['claim_06', '6. 其他请求', ''],
    ['claim_07', '7. 标的总额', ''],
  ];
}

function getFactsFields(typeId) {
  const FACTS = {
    lihun: [
      ['facts_01', '1. 婚姻关系基本情况', '结婚时间：\n生育子女情况： 双方生活情况：\n离婚事由：\n之前有无提起过离婚诉讼：'],
      ['facts_02', '2. 夫妻共同财产情况', ''],
      ['facts_03', '3. 夫妻共同债务情况', ''],
      ['facts_04', '4. 子女直接抚养情况', '（子女应归原告或者被告直接抚养的事由）'],
      ['facts_05', '5. 子女抚养费情况', '（原告或者被告应支付抚养费及相应金额、支付方式的事由）'],
      ['facts_06', '6. 子女探望权情况', '（不直接抚养子女一方应否享有探望权以及具体行使方式的事由）'],
      ['facts_07', '7. 赔 偿 / 补 偿 / 经 济 帮 助相关情况', '（符合离婚损害赔偿、离婚经济补偿或离婚经济帮助的相关事实等）'],
      ['facts_08', '8. 其他', ''],
      ['facts_09', '9. 请求依据', '（法律及司法解释的规定，要写明具体条文）'],
      ['facts_10', '10. 证据清单（可另附 页）', ''],
    ],
    mjjd: [
      ['facts_01', '2. 签订主体', '出借人： 借款人：'],
      ['facts_02', '3. 借款金额', '约定：\n实际提供：\n提供方式：现金□ 转账□ 其他：'],
      ['facts_03', '4. 借款期限', '是否到期：是□ 否□\n约定期限： 年 月 日起至 年 月 日止'],
      ['facts_04', '5. 借款利率', '利率□ %/ 年（季 / 月）（合同条款：第 条）'],
      ['facts_05', '6. 借款提供时间', '年 月 日， 元'],
      ['facts_06', '7. 还款方式', '到期一次性还本付息□\n按月计息、到期一次性还本□ 按季计息、到期一次性还本□ 按年计息、到期一次性还本□ 其他：'],
      ['facts_07', '8. 还款情况', '已还本金： 元\n已还利息： 元，还息至 年 月 日'],
      ['facts_08', '9. 是否存在逾期还款', '是□ 逾期时间： 至今已逾期\n否□'],
      ['facts_09', '10. 是否签订物的担保 （抵押、质押）合同', '是□ 签订时间：\n否□'],
      ['facts_10', '11. 担保人、担保物', '担保人： 担保物：'],
      ['facts_11', '12. 是否最高额担保（抵 押、质押）', '是□ 否□\n担保债权的确定时间： 担保额度：'],
      ['facts_12', '13. 是否办理抵押、质押 登记', '是□ 正式登记□\n预告登记□\n否□'],
      ['facts_13', '14. 是否签订保证合同', '是□ 签订时间： 保证人：\n主要内容：\n保证方式：一般保证□ 连带责任保证□\n否□'],
      ['facts_14', '15. 其他担保方式', '是□ 形式： 签订时间：\n否□'],
      ['facts_15', '16. 其他需要说明的内容', ''],
      ['facts_16', '17. 请求依据', '合同约定： 法律规定：'],
      ['facts_17', '18. 证据清单（可另附 页）', ''],
    ],
    jrjk: [
      ['facts_01', '2. 合同主体', '贷款人： 借款人：'],
      ['facts_02', '3. 借款金额', '约定：\n实际发放：'],
      ['facts_03', '4. 借款期限', '是否到期：是□ 否□\n约定期限： 年 月 日起至 年 月 日止'],
      ['facts_04', '5. 借款利率', '利率□ %/ 年（季 / 月）（合同条款：第 条） 逾期上浮□ %/ 年（合同条款：第 条）\n复利□ （合同条款：第 条）\n罚息（违约金）□ %/ 年（合同条款：第 条）'],
      ['facts_05', '6. 借款提供时间', '年 月 日， 元。'],
      ['facts_06', '7. 还款方式', '等额本息□ 等额本金□\n到期一次性还本付息□\n按月计息、到期一次性还本□ 按季计息、到期一次性还本□ 按年计息、到期一次性还本□ 其他□'],
      ['facts_07', '8. 还款情况', '已还本金： 元\n已还利息： 元，还息至 年 月 日'],
      ['facts_08', '9. 是否存在逾期还款', '是□ 逾期时间： 至今已逾期\n否□'],
      ['facts_09', '10. 是否签订物的担保 （抵押、质押）合同', '是□ 签订时间：\n否□'],
      ['facts_10', '11. 担保人、担保物', '担保人： 担保物：'],
      ['facts_11', '12. 是 否 最 高 额 担 保 （抵押、质押）', '是□ 否□\n担保债权的确定时间： 担保额度：'],
      ['facts_12', '13. 是否办理抵押、质 押登记', '是□ 正式登记□\n预告登记□\n否□'],
      ['facts_13', '14. 是否签订保证合同 / 保函', '是□ 签订时间： 保证人：\n主要内容：\n否□'],
      ['facts_14', '15. 保证方式', '一般保证□\n连带责任保证□'],
      ['facts_15', '16. 其他担保方式', '是□ 形式： 签订时间：\n否□'],
      ['facts_16', '17. 请 求 承 担 责 任 的 依据', '合同约定： 法律规定：'],
      ['facts_17', '18. 其他需要说明的内 容', ''],
      ['facts_18', '19. 证据清单（可另附 页）', ''],
    ],
    maimai: [
      ['facts_01', '2. 合同主体', '出卖人（卖方）： 买受人（买方）：'],
      ['facts_02', '3. 买 卖 标 的 物 情 况 （标的物名称、规格、 质量、数量等）', ''],
      ['facts_03', '4. 合同约定的价格及支 付方式', '单价 元；总价 元；\n以现金□ 转账□ 票据□（写明票据类型） 其他□ 方式\n一次性□ 分期□ 支付\n分期方式：'],
      ['facts_04', '5. 合同约定的交货时 间、地点、方式、风 险承担、安装、调试、 验收', ''],
      ['facts_05', '6. 合同约定的质量标准 及检验方式、质量异 议期限', ''],
      ['facts_06', '7. 合同约定的违约金 （定金）', '违约金□ 元（合同条款：第 条）\n定金□ 元（合同条款：第 条）\n迟延履行违约金□ %/ 日（合同条款：第 条）'],
      ['facts_07', '8. 价款支付及标的物交 付情况', '按期支付价款 元，逾期付款 元，逾期未付款 元 按期交付标的物 件，逾期交付 件，逾期未交付 件'],
      ['facts_08', '9. 是否存在迟延履行', '是□ 迟延时间： 逾期付款□ 逾期交货□\n否□'],
      ['facts_09', '10. 是否催促过履行', '是□ 催促情况： 年 月 日通过 方式进行了催促\n否□'],
      ['facts_10', '11. 买卖合同标的物有 无质量争议', '有□ 具体情况：\n无□'],
      ['facts_11', '12. 标的物质量规格或 履行方式是否存在不 符合约定的情况', '是□ 具体情况：\n否□'],
      ['facts_12', '13. 是否曾就标的物质 量问题进行协商', '是□ 具体情况：\n否□'],
      ['facts_13', '14. 是否通知解除合同', '是□ 具体情况：\n否□'],
      ['facts_14', '15. 被告应当支付的利 息、违约金、赔偿金', '利息□ 元\n违约金□ 元\n赔偿金□ 元\n共计 元 计算方式：'],
      ['facts_15', '16. 是否签订物的担保 （抵押、质押）合同', '是□ 签订时间：\n否□'],
      ['facts_16', '17. 担保人、担保物', '担保人： 担保物：'],
      ['facts_17', '18. 是 否 最 高 额 担 保 （抵押、质押）', '是□ 担保债权的确定时间：\n担保额度：\n否□'],
      ['facts_18', '19. 是否办理抵押、质 押登记', '是□ 正式登记□\n预告登记□\n否□'],
      ['facts_19', '20. 是否签订保证合同', '是□ 签订时间： 保证人： 主要内容：\n否□'],
      ['facts_20', '21. 保证方式', '一般保证□\n连带责任保证□'],
      ['facts_21', '22. 其他担保方式', '是□ 形式：\n否□'],
      ['facts_22', '23. 请求承担责任的依据', '合同约定： 法律规定：'],
      ['facts_23', '24. 其他需要说明的内 容', ''],
      ['facts_24', '25. 证据清单（可另附 页）', ''],
    ],
    ldzy: [
      ['facts_01', '1. 劳动合同签订情况', '（合同主体、签订时间、地点、合同名称等）'],
      ['facts_02', '2. 劳动合同履行情况', '（入职时间、用人单位、工作岗位、工作地点、合同约定的每月工资数额及 工资构成、办理社会保险的时间及险种、劳动者实际领取的每月工资数额 及工资构成、加班工资计算基数及计算方法、原告加班时间及加班费、年 休假等）'],
      ['facts_03', '3. 解除或终止劳动关系 情况', '（解除或终止劳动关系的原因、经济补偿 / 赔偿金数额等）'],
      ['facts_04', '4. 工伤情况', '（发生工伤时间、工伤认定情况、工伤伤残等级、工伤费用等）'],
      ['facts_05', '5. 劳动仲裁相关情况', '（申请劳动仲裁时间、仲裁请求、仲裁文书、仲裁结果等）'],
      ['facts_06', '6. 其他相关情况', '（如是否是农民工）'],
      ['facts_07', '7. 诉请依据', '（法律及司法解释的规定，要写明具体条文）'],
      ['facts_08', '8. 证据清单', ''],
    ],
    jtsg: [
      ['facts_01', '1. 交通事故发生情况', ''],
      ['facts_02', '2. 交通事故责任认定', ''],
      ['facts_03', '3. 机动车投保情况', ''],
      ['facts_04', '4. 请求依据', ''],
      ['facts_05', '5. 证据清单', ''],
    ],
    xyk: [
      ['facts_01', '1.信用卡办理情况（信用卡卡号、信用卡登记权利人、办卡时间、办卡行等）', ''],
      ['facts_02', '2.信用卡合约的主要约定', '透支金额：\n利息、罚息、复利、滞纳金、违约金、手续费等的计算标准：\n违约责任：\n解除条件：'],
      ['facts_03', '3.是否就信用卡合约主要条款进行提示注意', '是£ 提示说明的具体方式以及时间地点：\n否£'],
      ['facts_04', '4.被告逾期部分已还金额', '元'],
      ['facts_05', '5.被告逾期未还款金额', '逾期时间：\n截至 年 月 日，被告 欠付信用卡本金 元 、利息 元 、罚息 元、复利 元、滞纳金 元、违约金 元、手续费 元'],
      ['facts_06', '6.是否向被告进行通知和催收', '是£ 具体情况：\n否£'],
      ['facts_07', '7.是否签订物的担保（抵押、质押）合同', '是£ 签订时间：\n否£'],
      ['facts_08', '8.担保人、担保物', '担保人：\n担保物：'],
      ['facts_09', '9.是否最高额担保（抵押、质押）', '是£\n否£\n担保债权的确定时间：\n担保额度：'],
      ['facts_10', '10.是否办理抵押、质押登记', '是£ 正式登记£ 预告登记£\n否£'],
      ['facts_11', '11.是否签订保证合同', '是£ 签订时间： 保证人： 主要内容：\n否£'],
      ['facts_12', '12.保证方式', '一般保证 £\n连带责任保证£'],
      ['facts_13', '13.其他担保方式', '是£ 形式： 签订时间：\n否£'],
      ['facts_14', '14.请求承担责任的依据', '合同约定：\n法律规定：'],
      ['facts_15', '15.其他需要说明的内容', ''],
      ['facts_16', '16.证据清单', ''],
    ],
    wyfw: [
      ['facts_01', '1. 物业服务合同或前期 物业服务合同签订情 况（名 称、 编 号、 签 订时间、地点等）', ''],
      ['facts_02', '2. 签订主体', '业主 / 建设单位： 物业服务人：'],
      ['facts_03', '3. 物业项目情况', '坐落位置：\n面积： 所有权人：'],
      ['facts_04', '4. 约定的物业费标准', ''],
      ['facts_05', '5. 约定的物业服务期限', '年 月 日起至 年 月 日止'],
      ['facts_06', '6. 约定的物业费支付 方式', ''],
      ['facts_07', '7. 约定的逾期支付物业 费违约金标准', ''],
      ['facts_08', '8. 被告欠付物业费数额 及计算方式', '欠付物业费数额： 具体计算方式：'],
      ['facts_09', '9. 被告应付违约金数额 及计算方式', '应付违约金数额： 具体计算方式：'],
      ['facts_10', '10. 催缴情况', ''],
      ['facts_11', '11. 其他需要说明的内 容', ''],
      ['facts_12', '12. 请求依据', '合同约定： 法律规定：'],
      ['facts_13', '13. 证据清单（可另附 页）', ''],
    ],
    bxcss: [
      ['facts_01', '1. 财产保险合同的签 订情况（合同名称、主 体、签订时间、地点、 事故发生时，被保险人 与保险标的的关系等）', ''],
      ['facts_02', '2. 财产保险合同的主要 约定', '承保险种： 保险标的： 保险金额： 保费金额： 保险期间：\n免赔额或者免赔率：\n违约事由及违约责任： 特别约定：\n与争议相关的保险责任条款：\n与争议相关的免责条款： 其他：'],
      ['facts_03', '3. 是否依法就财产保险 合同中与投保人有重 大利害关系的条款进 行提示、说明', '是□\n否□ 事实与理由：'],
      ['facts_04', '5. 具体损失项目及其数 额（附理由）', ''],
      ['facts_05', '6. 财产保险合同的履行 情况', ''],
      ['facts_06', '7. 请求承担责任的依据', '合同约定： 法律规定：'],
      ['facts_07', '8. 其他需要说明的内容', ''],
      ['facts_08', '9. 证据清单', ''],
    ],
    zqxjcs: [
      ['facts_01', '1. 被告存在虚假陈述行 为的情况', '具体虚假陈述行为：\n虚假陈述行为实施日： 虚假陈述行为揭露日： 虚假陈述行为更正日： 虚假陈述基准日：'],
      ['facts_02', '2. 有无监管部门的认 定、处罚', '有□ 具体情况：\n无□'],
      ['facts_03', '3. 原告交易情况', '买入情况（日期、数量、单价）： 卖出情况（日期、数量、单价）：'],
      ['facts_04', '4. 虚假陈述的重大性', ''],
      ['facts_05', '5. 虚假陈述与原告交易 行为之间的因果关系', ''],
      ['facts_06', '6. 虚假陈述与原告损失 之间的因果关系', ''],
      ['facts_07', '7. 原告损失情况', ''],
      ['facts_08', '8. 请求发行人的控股股 东、实际控制人、董监 高、相关责任人员承担 连带责任的情况', ''],
      ['facts_09', '9. 请求保荐机构、承销 机构、律师事务所、会 计师事务所等其他机构 及其相关责任人员承担 连带责任的情况', ''],
      ['facts_10', '10. 请求承担责任的依据', ''],
      ['facts_11', '11. 其他需要说明的内 容', ''],
      ['facts_12', '12. 证据清单', ''],
    ],
    bzxbx: [
      ['facts_01', '1. 保证保险合同的签订 情况（合同名称、主体、 签订时间、地点等）', ''],
      ['facts_02', '2. 保证保险合同的主要 约定', '保证保险金额： 保费金额：\n保险期间：\n保险费缴纳方式： 理赔条件：\n理赔款项和未付保费的追索： 违约事由及违约责任：\n特别约定： 其他：'],
      ['facts_03', '3. 是否对被告就保证保 险合同主要条款进行 提示注意、说明', '是□ 提示说明的具体方式以及时间地点：\n否□'],
      ['facts_04', '4. 被告借款合同的主要 约定（借款金额、期 限、用途、利息标准、 还款方式、担保、违 约责任、 解除条件、 管辖约定）', ''],
      ['facts_05', '5. 被告逾期未还款情况', '自 年 月 日至 年 月 日，被告按约定还款，已还\n款 元，\n逾期但已还款 元，共归还本金 元，利息 元\n自 年 月 日起，开始逾期不还，截至 年 月 日，被\n告 欠 付 借 款 本 金 元 、 利 息 元、 罚 息 元、\n复 利 元、 滞 纳 金 元、 违 约 金 元、 手 续 费\n元\n明细：'],
      ['facts_06', '6. 保证保险合同的履行 情况', '原告于 年 月 日进行了理赔，代被告清偿债务，共赔款\n元，于 年 月 日取得权益转让确认书'],
      ['facts_07', '7. 追索情况', '原告于 年 月 日通知被告并向其追索\n被告已支付保费 元，归还借款 元； 尚欠保费 元，\n欠 付 借 款 本 金 元、 利 息 元、 罚 息 元、 复\n利 元、滞纳金 元、违约金 元、手续费 元\n明细：'],
      ['facts_08', '8. 请求承担责任的依据', '合同约定： 法律规定：'],
      ['facts_09', '9. 其他需要说明的内容', ''],
      ['facts_10', '10. 证据清单', ''],
    ],
    rongzi: [
      ['facts_01', '2. 合同主体', '出租人（卖方）： 承租人（买方）：'],
      ['facts_02', '3. 租赁物情况（租赁物 的选择、名称、规格、 质量、数量等）', ''],
      ['facts_03', '4. 合同约定的租金及支 付方式', '租金\n以现金□ 一次性□ 分期方式：'],
      ['facts_04', '5. 合同约定的租赁期 限、费用', '租赁期间自 年 月 日起至 年 月 日止\n除租金外产生的 费用，由 承担'],
      ['facts_05', '6. 到期后租赁物归属', '归承租人所有□\n归出租人所有□\n留购价款 元'],
      ['facts_06', '7. 合同约定的违约责任', ''],
      ['facts_07', '8. 是否约定加速到期 条款', '是□ 具体内容：\n否□'],
      ['facts_08', '9. 是否约定回收租赁物 条件', '是□ 具体内容：\n否□'],
      ['facts_09', '10. 是否约定解除合同 条件', '是□ 具体内容：\n否□'],
      ['facts_10', '11. 租赁物交付时间', '于 年 月 日交付租赁物'],
      ['facts_11', '12. 租赁物情况', '质量符合约定或者承租人的使用目的□ 存在瑕疵□ 具体情况：'],
      ['facts_12', '13. 租金支付情况', '自 年 月 日至 年 月 日，按约定缴纳租金，已付租\n金 元，\n逾期但已支付租金 元\n明细：'],
      ['facts_13', '14. 逾期未付租金情况', '自 年 月 日 起， 开 始 欠 付 租 金， 截 至 年 月 日，欠 付 租 金 元、 违 约 金 元， 滞纳金 元，损害赔偿金 元，共计 元\n明细：'],
      ['facts_14', '15. 是否签订物的担保 （抵押、质押）合同', '是□ 签订时间：\n否□'],
      ['facts_15', '16. 担保人、担保物', '担保人： 担保物：'],
      ['facts_16', '17. 是 否 最 高 额 担 保 （抵押、质押）', '是□ 担保债权的确定时间：\n担保额度：\n否□'],
      ['facts_17', '18. 是否办理抵押、质 押登记', '是□ 正式登记□\n预告登记□\n否□'],
      ['facts_18', '19. 是否签订保证合同', '是□ 签订时间： 保证人：\n主要内容：\n否□'],
      ['facts_19', '20. 保证方式', '一般保证□\n连带责任保证□'],
      ['facts_20', '21. 其他担保方式', '是□ 形式：签订时间：\n否□'],
      ['facts_21', '22. 请 求 承 担 责 任 的 依据', '合同约定： 法律规定：'],
      ['facts_22', '23. 其他需要说明的内 容', ''],
      ['facts_23', '24. 证据清单（可另附 页）', ''],
    ],
    fwmm: [
      ['facts_01', '1. 涉 及 房 屋 买 卖 合 同 关系的基本情况', '合同订立时间：\n房屋性质：商品房□ 经济适用房□ 自建房□ 其他：\n房屋位置： 房屋面积：\n房屋单价： 总价：\n房屋是否首次出售：是□ 否□ 是否为预售房：是□ 否□\n预售合同是否登记备案：是□ / 否□ 是否网签：是□ / 否□\n是否预告登记：是□ / 否□\n订立的合同性质：本约□ / 预约□\n是否已向被告发出解除 / 撤销合同的通知：是□（通知到达对方时间）否□ 解除 / 撤销事由：'],
      ['facts_02', '2. 购房款支付情况', '支付方式：按揭贷款□ 支付现金□ 以房抵债□ 其他：\n已支付 / 欠付购房款数额：\n是否已支付定金：是□ （定金数额 ）/ 否□\n是否包含精装修：是□ / 否□ 合同有关购房款支付的约定： 其他事由：'],
      ['facts_03', '3. 房屋交付情况', '是否已经实际交付：是□ / 否□\n是否存在房屋面积差：是□ / 否□\n是否包含车位或车库：是□ / 否□ 合同约定的交房时间：'],
      ['facts_04', '4. 房 屋 登 记 手 续 办 理 情况', '是否已经取得首次登记：是□ / 否□\n是否办理不动产转移登记手续：是□ / 否□ 是否约定逾期办证违约金：\n具体计算标准：'],
      ['facts_05', '5. 中介服务费情况', '应返还□ / 承担□ 中介服务费的事由'],
      ['facts_06', '6. 质 量 损 害 赔 偿 相 关 情况', '属于严重影响正常居住使用的质量问题□ 属于可修复的质量问题□\n是否还在质保期内：是□ 否□ 是否存在修复行为：是□ 否□ 是否通知维修：是□ 否□\n赔偿数额：'],
      ['facts_07', '7. 是 否 签 订 担 保 贷 款 （按揭）合同', '是□ 具体情况：\n否□'],
      ['facts_08', '8. 申 请 鉴 定 及 其 他 实 现债权费用的事实', '是□ 具体情况：\n否□'],
      ['facts_09', '9. 请求依据', '合同约定： 法律规定：'],
      ['facts_10', '10. 证据清单（可另附 页）', ''],
    ],
    fwzl: [
      ['facts_01', '2. 签订主体', '出租人： 承租人：'],
      ['facts_02', '3. 租赁标的物情况（坐 落位置、面积、产权情 况等）', ''],
      ['facts_03', '4. 合同约定的租赁期限', '自 年 月 日起至 年 月 日止'],
      ['facts_04', '5. 合同约定的租金及支 付方式', '租金： 元 / 月；总价 元：\n以现金□ 转账□ 票据□（写明票据类型） 其他□ 方式\n一次性□ 分期□ 支付\n分期方式：'],
      ['facts_05', '6. 其他费用约定（物业 费、水电燃气费用等）', '出租人负担： 承租人负担：'],
      ['facts_06', '7. 合同约定的违约责任', ''],
      ['facts_07', '8. 是否约定合同解除的 条件', '是□ 具体内容：\n否□'],
      ['facts_08', '9. 租赁物交付时间', '于 年 月 日交付租赁物'],
      ['facts_09', '10. 押金约定情况', '有□ 押金数额： ， 年 月 日已支付押金。\n无□'],
      ['facts_10', '11. 租金支付情况', '自 年 月 日至 年 月 日，按约定交纳租金，已付租金 元，逾期但已付租金 元\n明细：'],
      ['facts_11', '12. 逾期未付租金情况', '自 年 月 日起开始欠付租金，截至 年 月 日，欠付\n租金 元'],
      ['facts_12', '13. 其他需要说明的内 容', ''],
      ['facts_13', '14. 请求依据', '合同约定： 法律规定：'],
      ['facts_14', '15. 证据清单（可另附 页）', ''],
    ],
    jsgc: [
      ['facts_01', '2. 签订主体', '发包人： 承包人：\n出借资质的建筑企业： 实际施工人：'],
      ['facts_02', '3. 建设工程情况（工程 名称、所在地点、施工 范围、质量标准等）', ''],
      ['facts_03', '4. 合同约定的工程款及 支付方式', '综 合 单 价 □ 元； 固 定 单 价 □ 元； 固 定 总 价 □ 元；\n其他□:\n按施工进度支付工程款□;垫资施工□;其他□:\n以现金□ 转账□ 票据□（写明票据类型） 其他□ 方式\n质保金□ 元；质保金支付期限： 。'],
      ['facts_04', '5. 工期', '开工时间 ；竣工时间 ；工期 天。'],
      ['facts_05', '6. 合同约定的工程质量 标准及竣工验收程序', ''],
      ['facts_06', '7. 合同约定的违约金 （保证金）', '违约金□ 元（合同条款：第 条）\n保证金□ 元（合同条款：第 条）\n迟延履行违约金□ %/ 日（合同条款：第 条）'],
      ['facts_07', '8. 工程款支付情况', '工程总价 元；已支付工程款 元；\n欠 / 超付工程款 元。\n欠 / 超付工程款利息： 元。'],
      ['facts_08', '9. 建设工程质量情况', '工程质量是否合格：是□ 否□\n工程质量问题： 。\n工程质量造成损失： 元。'],
      ['facts_09', '10. 建设工程交付情况', '工程是否迟延交付：是□ 否□ 交付时间 。\n工程迟延交付造成损失： 元。'],
      ['facts_10', '11. 停窝工等情况', '工程是否停窝工：是□ 否□\n工程停窝工造成损失： 元。'],
      ['facts_11', '12. 是否主张过建设工 程价款优先受偿权', '是□ 主张情况： 年 月 日通过 方式主张了建设工程价\n款优先受偿权\n否□'],
      ['facts_12', '13. 其他需要说明的内 容', ''],
      ['facts_13', '14. 请求依据', '合同约定： 法律规定：'],
      ['facts_14', '15. 证据清单', ''],
    ],
    rsbx: [
      ['facts_01', '1. 人身保险合同的签订 情况（合同名称、主 体、签订时间、地点、 保险合同订立时投保人 与被保险人的关系等）', ''],
      ['facts_02', '2. 人身保险合同的主要 约定', '承保险种： 投保人：\n被保险人： 投保人与被保险人的关系：\n受益人： 受益人与被保险人的关系：\n保险责任： 保险金额： 保费金额： 保险期间：\n免赔额或者免赔率：\n违约事由及违约责任： 特别约定：\n与争议相关的保险责任条款： 与争议相关的免责条款：\n其他：'],
      ['facts_03', '3. 是否依法就人身保险 合同中与投保人有重 大利害关系的条款进 行提示、说明', '是□\n否□ 事实与理由：'],
      ['facts_04', '4. 保险事故发生的情况 （事故发生时间及经过 等；意外事故导致受伤 或死亡的，写明出警情 况，公安机关对于意外 死亡的证明情况）', ''],
      ['facts_05', '5. 具体损失项目及其数 额（附计算方式及理由）', ''],
      ['facts_06', '6. 人身保险合同的履行 情况', ''],
      ['facts_07', '7. 请求承担责任的依据', '合同约定： 法律规定：'],
      ['facts_08', '8. 其他需要说明的内容', ''],
      ['facts_09', '9. 证据清单', ''],
    ],
    zebx: [
      ['facts_01', '1. 责任保险合同的签订 情况（合同名称、主 体、签订时间、地点、 事故发生时被保险人 与保险标的的关系等）', ''],
      ['facts_02', '2. 责任保险合同的主要 约定', '承保险种：□雇主责任险 □机动车第三者责任险 □车上人员责任险\n□物流责任险 □其他 保险责任：\n保险金额： 保费金额： 保险期间：\n免赔额或者免赔率：\n违约事由及违约责任： 特别约定：\n与争议相关的保险责任条款： 与争议相关的免责条款：\n其他：'],
      ['facts_03', '3. 是否依法就责任保险 合同中与投保人有重 大利害关系的条款进 行提示、说明', '是□\n否□ 事实与理由：'],
      ['facts_04', '5. 具体损失项目及其数 额（附计算方式及理由）', ''],
      ['facts_05', '6. 责任保险合同的履行 情况', ''],
      ['facts_06', '7. 请求承担责任的依据', '合同约定： 法律规定：'],
      ['facts_07', '8. 其他需要说明的内容', ''],
      ['facts_08', '9. 证据清单', ''],
    ],
    xzcf: [
      ['facts_01', '1. 被诉行政处罚的种类', '□警告 □通报批评 □罚款 □没收违法所得、没收非法财物\n□暂扣许可证、降低资质等级、吊销许可证\n□限制开展生产经营活动、责令停产停业、责令关闭、限制从业\n□行政拘留\n□其他行政处罚：'],
      ['facts_02', '2. 行政处罚决定文号及 作出时间', '文号：\n时间： 年 月 日'],
      ['facts_03', '3. 行政处罚行为是否存 在违法之处', '□是 具体情形： □否'],
      ['facts_04', '4. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_05', '5. 其他需要说明的内容', ''],
      ['facts_06', '6. 证据清单', ''],
    ],
    xzqzzx: [
      ['facts_01', '1. 被诉行政强制执行的 方式', '□加处罚款或者滞纳金\n□划拨存款、汇款\n□拍卖查封扣押的场所、设施或者财物\n□处理查封扣押的场所、设施或者财物\n□排除妨碍\n□恢复原状 □代履行\n□强制拆除房屋或者设施\n□强制清除地上物 □其他：'],
      ['facts_02', '2. 行政强制执行行为作 出时间', '年 月 日'],
      ['facts_03', '3. 行政强制执行行为是 否存在违法之处', '□是 具体情形： □否'],
      ['facts_04', '4. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_05', '5. 其他需要说明的内容', ''],
      ['facts_06', '6. 证据清单', ''],
    ],
    xzxk: [
      ['facts_01', '1. 申请人提出行政许可 的时间', '年 月 日'],
      ['facts_02', '2. 行政许可决定文号及 作出时间', '文号：\n时间： 年 月 日'],
      ['facts_03', '3. 行政许可行为是否存 在违法之处', '□是 具体情形： □否'],
      ['facts_04', '4. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_05', '5. 其他需要说明的内容', ''],
      ['facts_06', '6. 证据清单', ''],
    ],
    fwzs: [
      ['facts_01', '1. 被告作出房屋征收决 定的文号及时间', '文号：\n时间： 年 月 日'],
      ['facts_02', '2. 原告知道被告作出房 屋征收决定的时间', '年 月 日'],
      ['facts_03', '3. 房屋征收决定是否存 在违法之处', '□是 具体情形： □否'],
      ['facts_04', '4. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_05', '5. 其他需要说明的内容', ''],
      ['facts_06', '6. 证据清单', ''],
    ],
    gsbx: [
      ['facts_01', '1. 职工与用人单位是否 存在劳动关系', '□是 □否'],
      ['facts_02', '2. 本案起诉前已经就是 否存在劳动关系申请劳 动仲裁或提起民事诉讼', '□是 □否'],
      ['facts_03', '3. 职工工作岗位', ''],
      ['facts_04', '4. 职工发生事故伤害或 者被诊断、鉴定为职 业病时间', '年 月 日'],
      ['facts_05', '5. 行政机关作出认定工 伤决定书或者不予认 定工伤决定书的文号 及时间', '文号：\n时间： 年 月 日'],
      ['facts_06', '6. 当事人收到关于工 伤决定等文书的时间 （如未收到关于工伤决 定等文书，请填写提 出履责申请的时间）', '年 月 日'],
      ['facts_07', '7. 工伤决定是否存在违 法之处', '□是 具体情形： □否'],
      ['facts_08', '8. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_09', '9. 其他需要说明的内容', ''],
      ['facts_10', '10. 证据清单（可另附 页）', ''],
    ],
    zfxxgk: [
      ['facts_01', '1. 申请时间', '年 月 日'],
      ['facts_02', '2. 申请人申请公开的政 府信息内容', '列明申请公开的政府信息的名称、文号或者便于行政机关查询的其他特征 性描述：'],
      ['facts_03', '3. 申请人要求提供政府 信息的形式', '□纸质材料\n□电子数据\n□查阅、抄录 其他：'],
      ['facts_04', '4. 行政机关作出政府信 息公开答复的时间', '年 月 日'],
      ['facts_05', '5. 政府信息公开答复的 文号及内容', '文号： 内容：'],
      ['facts_06', '6. 政府信息公开行为是 否存在违法之处', '□是 具体情形： □否'],
      ['facts_07', '7. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_08', '8. 其他需要说明的内容', ''],
      ['facts_09', '9. 证据清单', ''],
    ],
    xzfy: [
      ['facts_01', '1. 提出行政复议申请时间', '年 月 日'],
      ['facts_02', '2. 行政复议请求', '请求内容：'],
      ['facts_03', '3. 行政复议决定文号及作出时间', '文号： 时间：'],
      ['facts_04', '4. 行政复议决定是否存在违法之处', '□是 具体情形： □否'],
      ['facts_05', '5. 是否就同一争议提出过其他行政复议申请或者诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_06', '6. 其他需要说明的内容', ''],
      ['facts_07', '7. 证据清单', ''],
    ],
    xzxy: [
      ['facts_01', '1. 协议签订情况', '名称： 编号：\n签订时间： 年 月 日\n签订主体：'],
      ['facts_02', '2. 主要内容', ''],
      ['facts_03', '3. 协议履行情况', ''],
      ['facts_04', '4. 行政协议的订立、履 行、变更、终止等是 否存在违法之处', '□是 具体情形： □否'],
      ['facts_05', '5. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_06', '6. 其他需要说明的内容', ''],
      ['facts_07', '7. 证据清单', ''],
    ],
    xzbc: [
      ['facts_01', '1. 被告作出补偿决定的文号及时间', '文号：\n时间： 年 月 日'],
      ['facts_02', '2. 原告知道被告作出补偿决定的时间', '年 月 日'],
      ['facts_03', '3. 原告或他人是否对案涉房屋征收决定提起行政诉讼及裁判结果', '□是\n裁判结果： □否'],
      ['facts_04', '4. 被告是否具有作出补偿决定的职权', '□是 □否\n具体理由：'],
      ['facts_05', '5. 原告对被告决定的补偿金额和支付期限有无异议', '□有\n具体理由： □无'],
      ['facts_06', '6. 原告对被告决定的用于产权调换房屋的地点和面积有无异议', '□有\n具体理由： □无'],
      ['facts_07', '7. 原告对被告决定的 搬迁费、临时安置费、 签约奖励费、营业损 失等有无异议', '□有\n具体理由： □无'],
      ['facts_08', '8. 原告对被告决定的搬迁期限、过渡方式和 过渡期限有无异议', '□有\n具体理由： □无'],
      ['facts_09', '9. 是否就同一争议申请过复议或者提起过其他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_10', '10. 其他需要说明的内容', ''],
      ['facts_11', '11. 证据清单', ''],
    ],
    xzpc: [
      ['facts_01', '1. 被告是否做出赔偿决定', '□是\n赔偿决定文号：\n赔偿决定作出时间： 年 月 日\n□否'],
      ['facts_02', '2. 原告主张的加害行为是否已经复议或诉讼确认违法', '□是\n确违具体情况： □否'],
      ['facts_03', '3. 请求赔偿的依据、赔偿方式及赔偿内容', ''],
      ['facts_04', '4. 是否就同一争议申请过复议或者提起过其他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_05', '5. 其他需要说明的内容', ''],
      ['facts_06', '6. 证据清单', ''],
    ],
    xzbllzz: [
      ['facts_01', '1. 申请履行法定职责的 方式', '□口头提出 □书面提出'],
      ['facts_02', '2. 申请履行法定职责的 时间', '年 月 日'],
      ['facts_03', '3. 申请履行法定职责的 内容', ''],
      ['facts_04', '4. 行政机关是否在法定 期限内履行了法定职责', '□是 □否'],
      ['facts_05', '5. 行政机关是否作出了 书面处理决定', '□是 具体时间： 年 月 日\n□否'],
      ['facts_06', '6. 是否就同一争议申请 过复议或者提起过其 他诉讼', '□是 列明案号、时间、受理机关、处理结果等具体情况： □否'],
      ['facts_07', '7. 其他需要说明的内容', ''],
      ['facts_08', '8. 证据清单', ''],
    ],
    xswrw: [
      ['facts_01', '1. 事实（被告人实施侮辱行为的时间、地点、手段、情节、危害后果等，被告人通过网络实施的， 自诉人如果与网络平台存在相关诉讼，请一并写明诉讼情况）： 2. 理由（被告人涉嫌犯罪、承担附带民事赔偿责任的法律依据）：', ''],
      ['facts_02', '证据清单 （证据材料另附）', ''],
      ['facts_03', '1. 证明被告人实施侮辱行为、构成犯罪等证据材料 2.（提起附带民事诉讼的）证明因被告人实施侮辱行为给自诉人造成物质损失的证据材料 3. 其他证据材料', ''],
      ['facts_04', '是否同意调解', ''],
      ['facts_05', '自诉部分', '同意□ 不同意□ 暂不确定□'],
      ['facts_06', '附带民事部分', '同意□ 不同意□ 暂不确定□'],
    ],
    xsfb: [
      ['facts_01', '1. 事实（被告人实施诽谤行为的时间、地点、手段、情节、危害后果等，被告人通过网络实施的， 自诉人如果与网络平台存在相关诉讼，请一并写明诉讼情况）： 2. 理由（被告人涉嫌犯罪、承担附带民事赔偿责任的法律依据）：', ''],
      ['facts_02', '证据清单 （证据材料另附）', ''],
      ['facts_03', '1. 证明被告人实施诽谤行为、构成犯罪等证据材料。 2.（提起附带民事诉讼的）证明因被告人实施诽谤行为给自诉人造成物质损失的证据材料。 3. 其他证据材料。', ''],
      ['facts_04', '是否同意调解', ''],
      ['facts_05', '自诉部分', '同意□ 不同意□ 暂不确定□'],
      ['facts_06', '附带民事部分', '同意□ 不同意□ 暂不确定□'],
    ],
    xschh: [
      ['facts_01', '1. 事实（主要包括自诉人与被告人的婚姻情况、被告人重婚的时间、对象、重婚对象是否明知等）： 2. 理由（被告人涉嫌犯罪、承担附带民事赔偿责任的法律依据）：', ''],
      ['facts_02', '证据清单 （证据材料另附）', ''],
      ['facts_03', '1. 自诉人与被告人结婚证等证明婚姻关系的证据材料。 2. 证明被告人重婚的书证、证人证言、视听资料、电子数据等证据材料。 3.（提起附带民事诉讼的）证明因被告人重婚行为给自诉人造成物质损失的证据材料。 4. 其他证据材料。', ''],
      ['facts_04', '是否同意调解', ''],
      ['facts_05', '自诉部分', '同意□ 不同意□ 暂不确定□'],
      ['facts_06', '附带民事部分', '同意□ 不同意□ 暂不确定□'],
    ],
    xsjbzx: [
      ['facts_01', '1. 事实： （1）自诉人认为被告人拒不执行的生效判决书、裁定书的案号、生效日期、作出法院的名称； （2）自诉人向法院申请执行的情况（如申请执行的裁判文书涉及其他人员 / 单位，请写明相关人员 / 单位的姓名和联系方式）； （3）被告人是否有执行能力； （4）自诉人向公安机关或人民检察院提出控告的情况； （5）公安机关或人民检察院的答复情况（如是否作出《不予立案通知书》或《不起诉决定书》，是否 不接收报案材料等）； （6）其他有关事实。 2. 理由（被告人涉嫌犯罪、承担附带民事赔偿责任的法律依据）：', ''],
      ['facts_02', '证据清单 （证据材料另附）', ''],
      ['facts_03', '1. 自诉人申请执行的裁判文书。 2. 公安机关、检察机关不予答复的相关材料。 3.（提起附带民事诉讼的）证明因被告人实施拒不执行判决、裁定行为给自诉人造成物质损失的证 据材料。 4. 其他证据材料。', ''],
    ],
    shangbiao: [
      ['facts_01', '1. 原告主体情况', '1. 商标注册人□\n2. 利害关系人□: 被许可人□:\n①独占使用许可合同的被许可人□\n②排他使用许可合同的被许可人□:\n和权利人共同起诉□ 单独起诉□（权利人已起诉□ 权利人未起诉□)\n③普通使用许可合同的被许可人□:\n和权利人共同起诉□ 单独起诉□（权利人书面授权单独起诉□;权利人 未授权单独起诉□)\n3. 其他利害关系人□ 具体情形：'],
      ['facts_02', '2. 原告商标权属事实', '1. 权利商标情况（商标号、标志图样、核定商品 / 服务类别、申请时间、核 准注册时间、有效期等）：\n2. 是否主张驰名：是□ 否□\n主张驰名的商标是否系注册商标：是□（商标号： ） 否□\n3. 效力状态（是否存在或正处于商标授权确权程序）：'],
      ['facts_03', '3. 原告商标权使用及知 名度事实', ''],
      ['facts_04', '4. 被告商标侵权事实 （包括持续时间、使用 场合、表现形式、主 观故意程度及损害后 果等）', '1. 被告侵权行为表现形式、使用的侵权标识图样及比对意见（结合法律依 据的具体项目陈述，并附图样及证据）：\n2. 被告主观故意程度及具体情节：\n3. 损害后果：\n4. 是否存在适用惩罚性赔偿的事由：\n5. 其他：'],
      ['facts_05', '5. 其他事项', ''],
      ['facts_06', '6. 证据清单', ''],
      ['facts_07', '关联案件信息 （原告依据本案注册商标提起的其他侵害商标权诉讼）', ''],
    ],
    fmzl: [
      ['facts_01', '1. 原告主体情况', '专利权人□：原始取得□ 继受取得□\n是否存在共有权人：是□（共有权人是否明确表示同意起诉： 是□ 否□)\n否□ 利害关系人□：被许可人□：专利权人：\n获得许可时间： 许可期限：\n（1）专利独占实施被许可人□\n（2）专利排他实施被许可人□：和专利权人共同起 诉□ 单独起诉（专利权人明确表示不起诉）□\n（3）专利普通实施被许可人□：和专利权人共同起 诉□ 单独起诉（专利权人书面授权单独起诉）□\n其他利害关系人□ 具体情形：'],
      ['facts_02', '2. 权利基础状况', '专利号：\n专利名称：\n专利类型：发明专利\n专利领域：机械□ 电学□ 通信□ 化学□ 医药生物□ 光电□ 材料□ 其他□ 专利申请日：\n专利优先权日： 授权公告日：\n据以主张权利的权利要求序号：\n据以主张权利的权利要求效力状态：有效□ 无效□ 终止□'],
      ['facts_03', '4. 被诉侵权行为', '侵权产品：（写明产品型号等）\n侵权行为方式：（具体写明系为生产经营目的制造、使用、许诺销售、销 售、进口专利产品，或者使用专利方法以及使用、许诺销售、销售、进口 依照该专利方法直接获得的产品等行为方式中的哪些行为）\n侵权行为期间：\n被诉侵权行为具体情形：（写明发现方式、渠道）'],
      ['facts_04', '5. 共同侵权', '有□ 主要事实与理由：（一并写明共同侵权主体之间是否存在关联关系）\n无□'],
      ['facts_05', '6. 其他', '有□ 内容：\n无□'],
      ['facts_06', '【责任承担】1. 停止侵害', '被告应当立即停止侵害。具体主张：（一并说明本案诉讼期间被诉侵权行为 是否仍在进行）'],
      ['facts_07', '【责任承担】2. 赔偿责任', '补偿性赔偿： 元。选择：\n原告受损□ 元\n被告获利□ 元\n许可使用费□ 元\n（基数： 元，倍数： ）\n法定赔偿□ 元\n惩罚性赔偿： 元 （基数： 元，\n倍数： ）\n（如不主张，可不填）\n维权合理开支： 元。包括： 律师费□ 元\n公证费□ 元\n差旅费□ 元\n其他费用□ 元\n（如不主张，可不填）'],
      ['facts_08', '【责任承担】3. 连带责任', '有□ 内容：被告一 ××、被告二 ×× 构成共同侵权，应当连带赔偿原告 经济损失 × 元、维权合理开支 × 元。具体理由：\n无□'],
      ['facts_09', '【责任承担】4. 其他责任', '有□ 内容：\n无□'],
      ['facts_10', '【责任承担】5. 法律依据', ''],
    ],
    wgsj: [
      ['facts_01', '1. 原告主体情况', '外观设计专利权人□\n1. 原始取得□ 2. 继受取得□ 原权利人信息：\n转让时间： 其它：\n利害关系人□:\n1. 被许可人□:\n①独占使用许可合同的被许可人□\n②排他使用许可合同的被许可人□：和权利人共同起诉□ 单独起诉□ （权利人已起诉□ 权利人未起诉□)\n③普通使用许可合同的被许可人□：和权利人共同起诉□ 单独起诉□ （权利人书面授权单独起诉□ 权利人未授权单独起诉□)\n2. 其他利害关系人□ 具体情形：'],
      ['facts_02', '2. 权利基础情况', '专利号：\n专利名称：\n专利申请日：\n专利优先权日： 授权公告日：\n据以主张权利的权利要求效力状态：有效□ 无效□ 终止□'],
      ['facts_03', '3. 外观设计专利权评价 报告', '是否提交报告 □是\n□全部外观设计未发现存在不符合授予专利权条件的缺陷。\n□全部外观设计不符合授予专利权条件。\n□该外观设计的 不符合授予专利权条件， 未发现存在不符合授予 专利权条件的缺陷。\n□否'],
      ['facts_04', '4. 被告侵犯外观设计专 利的事实', '1. 被诉侵权产品实物（附录像，如有）\n2. 被诉侵权产品图片\n3. 被告侵权行为方式证据\n4. 被告侵权期间证据\n5. 被告财务报表（如无，暂可不交）\n6. 其他证据'],
      ['facts_05', '5. 证据清单', ''],
      ['facts_06', '关联案件信息', ''],
    ],
    zwxpz: [
      ['facts_01', '1. 原告主体情况', '品种权人□：原始取得□ 继受取得□\n是否存在共有权人：是□（共有权人是否明确表示同意起诉： 是□ 否□)\n否□ 利害关系人□：被许可人□：品种权人：\n获得许可时间： 许可期限：\n（1）品种权独占实施被许可人□\n（2）品种权排他实施被许可人□：和品种权 人共同起诉□ 单独起诉（品种权人明确表 示不起诉）□\n（3）品种权普通实施被许可人□：和品种权 人共同起诉□ 单独起诉（品种权人书面授 权单独起诉）□\n其他利害关系人□ 具体情形：'],
      ['facts_02', '2. 权利基础状况', '品种权号： 品种名称：\n初步审查合格公告日： 授予品种权日：\n效力状态：有效□ 无效□ 终止□'],
      ['facts_03', '3. 被诉侵权行为', '侵权产品：（写明产品名称等）\n侵权行为方式：（具体写明系生产、繁殖和为繁殖而进行处理、许诺销售、 销售、进口、出口以及为实施上述行为储存该授权品种的繁殖材料，为商 业目的将该授权品种的繁殖材料重复使用于生产另一品种的繁殖材料等行 为方式中的哪些行为）\n侵权行为期间：\n被诉侵权行为具体情形：（写明发现方式、渠道）'],
      ['facts_04', '4. 共同侵权', '有□ 主要事实与理由：（一并写明共同侵权主体之间是否存在关联关系）\n无□'],
      ['facts_05', '5. 侵权产品检测', '检测时间： 检测机构： 检测方法：\n检验报告编号：\n检验报告结论：（概述）'],
      ['facts_06', '6. 其他', '有□ 内容：\n无□'],
      ['facts_07', '【责任承担】1. 停止侵害', '被告应当立即停止侵害。具体主张：（一并说明本案诉讼期间被诉侵权行为 是否仍在进行）'],
      ['facts_08', '【责任承担】2. 赔偿责任', '补偿性赔偿： 原告受损□\n被告获利□\n许可使用费□\n（基数： 法定赔偿□\n惩罚性赔偿： 元 （基数： 元， 倍数： ）\n（如不主张，可不填）\n维权合理开支： 元。包括： 律师费□ 元\n公证费□ 元\n差旅费□ 元\n其他费用□ 元\n（如不主张，可不填）'],
      ['facts_09', '【责任承担】3. 连带责任', '有□ 内容：被告一 ××、被告二 ×× 构成共同侵权，应当连带赔偿原告 经济损失 × 元、维权合理开支 × 元。具体理由： … …\n无□'],
      ['facts_10', '【责任承担】4. 其他责任', '有□ 内容：\n无□'],
      ['facts_11', '【责任承担】5. 法律依据', ''],
    ],
    zhuzuoquan: [
      ['facts_01', '1. 著作权主体', '原告著作权主体身份为： 1. 作者或视为作者的法人或非法人组织□ 2. 继\n受主体：被许可人□（原告与著作权人签订授权合同的时间、合同名称及 有效期及权限、区域 ，获得授权的性质：独占□ 排他□ 普通 □);受让人□;继承人□;受遗赠人□\n作品性质属于： 1. 合作作品□ 2. 汇编作品□ 3. 演绎作品□ 4. 职务作 品□ 5. 委托作品□ 6. 其他□。'],
      ['facts_02', '2. 著作权客体', '作品名称为： ，作品完成时间： ，作品首次公开发表时 间、地方及方式： ，是否进行版权登记：是□ 否□,登记时\n间： ，作品类别为： 1. 文字作品□ 2. 口述作品□ 3. 音乐、戏 剧、曲艺、舞蹈、杂技艺术作品□ 4. 美术、建筑作品□ 5. 摄影作品□ 6. 视听作品☑ 7. 工程设计图、产品设计图、地图、示意图等图形作品和 模型作品□ 8. 计算机软件□ 9. 符合作品特征的其他智力成果□。\n请提供权属证明。'],
      ['facts_03', '3. 涉嫌侵害著作人身权 或财产权的种类', '1. 发表权□ 2. 署名权□ 3. 修改权□ 4. 保护作品完整权□ 5. 复制 权□ 6. 发行权□ 7. 出租权□ 8. 展览权□ 9. 表演权□ 10. 放映权□ 11. 广播权□ 12. 信息网络传播权（原告是否向被告发出侵权通知：\n□是 □否，时间及内容： ）□ 13. 摄制权□ 14. 改编权□ 15. 翻 译权□ 16. 汇编权□ 17. 其他□'],
      ['facts_04', '4. 被诉侵权行为方式', '□ 1. 未经著作权人许可，发表其作品的\n□ 2. 未经合作作者许可，将与他人合作创作的作品当作自己单独创作的作 品发表的\n□ 3. 没有参加创作，为谋取个人名利，在他人作品上署名的\n□ 4. 歪曲、篡改他人作品的\n□ 5. 剽窃他人作品的\n□ 6. 未经著作权人许可，以展览、摄制电影和以类似摄制电影的方法使用 作品，或者以改编、翻译、注释等方式使用作品的\n□ 7. 使用他人作品，应当支付报酬而未支付的\n□ 8. 未经电影作品和以类似摄制电影的方法创作的作品、计算机软件、录 音录像制品的著作权人或者与著作权有关的权利人许可，出租其作品或者 录音录像制品的\n□ 9. 未经出版者许可，使用其出版的图书、期刊的版式设计的\n□ 10. 未经表演者许可，从现场直播或者公开传送其现场表演，或者录制其 表演的\n□ 11. 录音录像制作者权侵权、广播组织权侵权\n□ 12. 其他\n（可补充被告使用作品的具体方式及载体，比对证据等内容及依据）'],
      ['facts_05', '5. 被诉侵权行为发生的 时间、地点', ''],
      ['facts_06', '6. 是否发送侵权通知', '具体情况，□是 □否，依据（证据）'],
      ['facts_07', '7. 其他需要说明的内容', '具体情况，依据（证据）'],
      ['facts_08', '8. 证据清单', ''],
      ['facts_09', '关联案件信息', ''],
    ],
    jishu: [
      ['facts_01', '1. 技术合同的签订情况 （技术领域，项目的名 称，标的的内容、范 围和要求，履行的计 划、地点和方式，技 术成果的归属和收益 的分配办法，验收标 准和方法等）', ''],
      ['facts_02', '2. 合同签订主体', ''],
      ['facts_03', '3. 约定的合同期限', '年 月 日起至 年 月 日止'],
      ['facts_04', '4. 约 定 的 给 付 价 款、 报酬、使用费及支付 方式', ''],
      ['facts_05', '5. 约定的给付价款利息 （违约金）及计算方式', ''],
      ['facts_06', '6. 技术合同履行情况', ''],
      ['facts_07', '7. 其他情况及依据', ''],
      ['facts_08', '8. 证据清单', ''],
      ['facts_09', '关联案件信息', ''],
    ],
    bzdj: [
      ['facts_01', '1. 原告主体情况', '具体情形：'],
      ['facts_02', '2. 原告主张的权益基 础或特定行为的损害 对象', '有□ 内容：\n无□'],
      ['facts_03', '3. 被告实行不正当竞争 行为的具体事实（包 括时间、地点、表现 形式、具体内容、主 观故意程度和损害后 果等）', ''],
      ['facts_04', '4. 其他情况', ''],
      ['facts_05', '5. 证据清单', ''],
      ['facts_06', '关联案件信息', ''],
    ],
    longduan: [
      ['facts_01', '1. 被诉垄断行为', '具体内容：（综述具体所诉垄断行为）。\n实施垄断行为期间：\n是否为行政处罚的后继诉讼：是□ （被诉行为及持续时间是否完全涵盖行 政处罚所涉期间：是□ 否□；被告是否为 行政处罚确定的实施主体：是□ 否□）\n否□'],
      ['facts_02', '2. 共同侵权', '有□ 主要事实与理由：（一并写明共同侵权主体之间是否存在关联关系）\n无□'],
      ['facts_03', '3. 相关市场界定', '本案相关市场为 … …（包括具体时间范围内的商品市场、地域市场）。 具体说明：\n（原告主张被诉垄断行为属于反垄断法第十七条第一项至第五项和第十 八条第一款第一项、第二项规定情形的，可以不对相关市场界定提供证据）'],
      ['facts_04', '4. 具体垄断行为', '被告达成 / 实施了横向垄断协议 / 纵向垄断协议 / 轴辐协议，具体 为： … …。上述协议产生了排除、限制竞争效果，具体分析：\n（适用于垄断协议纠纷）\n被告在 …… 相关市场，具有市场支配地位，具体分析：\n被告实施滥用市场支配地位的行为，具体包括：\n垄断定价□ 具体分析：\n掠夺定价□ 具体分析：\n拒绝交易□ 具体分析：\n限定交易□ 具体分析：\n捆绑交易□ 具体分析：\n差别待遇□ 具体分析：\n被告的行为产生了排除、限制竞争效果，具体分析：\n（适用于滥用市场支配地位纠纷）'],
      ['facts_05', '5. 其他', ''],
      ['facts_06', '【责任承担】1. 停止垄断行为', '被告应当立即停止垄断行为。具体说明：'],
      ['facts_07', '【责任承担】2. 赔偿责任', '经济损失： 元\n计算方法：\n维权合理开支： 元。包括：\n律师费□ 元\n经济分析费□ 元\n市场调查费□ 元\n其他费用□ 元\n（如不主张，可不填）'],
      ['facts_08', '【责任承担】3. 连带责任', '有□ 内容：被告一 ××、被告二 ×× 构成共同侵权，应当连带赔偿原告 经济损失 × 元、维权合理开支 × 元。具体理由： … …\n无□'],
      ['facts_09', '【责任承担】4. 其他责任', '有□ 内容：\n无□'],
      ['facts_10', '【责任承担】5. 法律依据', ''],
    ],
    syms: [
      ['facts_01', '1. 原告主体情况', '商业秘密权利人□ 原始取得□\n继受取得□\n受让取得□\n其他取得□ 具体情况： 利害关系人□:\n1. 被许可人□:\n①独占使用许可合同的被许可人□\n②排他使用许可合同的被许可人□：和权利人共同起诉□ 单独起诉□ （权利人已起诉□ 权利人未起诉□)\n③普通使用许可合同的被许可人□：和权利人共同起诉□ 单独起诉□ （权利人书面授权单独起诉□ 权利人未授权单独起诉□)\n2. 其他利害关系人□ 具体情形：'],
      ['facts_02', '2. 原告主张的商业秘密 类型', '技术信息□ 经营信息□ 其他商业信息□\n载体：\n形成时间： 具体内容：'],
      ['facts_03', '3. 原告主张的商业秘密 符合法定条件', '1. 不为公众所知悉 □是 □否 具体情况：\n2. 采取了保密措施 □是 □否 具体情况：\n3. 具有商业价值 □是 □否 具体情况：'],
      ['facts_04', '4. 被告侵犯商业秘密的 事实（包括时间、地 点、表现形式、具体 内容、主观故意程度 和损害后果等）', '□ 1. 以盗窃、贿赂、欺诈、胁迫、电子侵入或者其他不正当手段获取权利 人的商业秘密； 具体情况，依据（证据）：\n□ 2. 披露、使用或者允许他人使用以前项手段获取的权利人的商业秘 密； 具体情况，依据（证据）：\n□ 3. 违反保密义务或者违反权利人有关保守商业秘密的要求，披露、使用 或者允许他人使用其所掌握的商业秘密； 具体情况，依据（证据）：\n□ 4. 教唆、引诱、帮助他人违反保密义务或者违反权利人有关保守商业 秘密的要求，获取、披露、使用或者允许他人使用权利人的商业秘密； 具体情况，依据（证据）：\n□ 5. 经营者以外的其他自然人、法人和非法人组织实施的侵犯商业秘密行 为； 具体情况，依据（证据）：\n□ 6. 第三人明知或者应知商业秘密权利人的员工、前员工或者其他单位、 个人实施侵犯商业秘密行为，仍获取、披露、使用或者允许他人使用该商 业秘密的； 具体情况，依据（证据）：\n□ 7. 其他侵犯商业秘密的行为。 具体情况，依据（证据）：'],
      ['facts_05', '5. 侵犯商业秘密行为与 原告损失之间的因果 关系', '具体情况，依据（证据）'],
      ['facts_06', '6. 侵害技术秘密案件中 的技术比对分析', '具体主张密点或整体技术方案、比对分析意见（可另附页）'],
      ['facts_07', '7. 其他情况及依据', ''],
      ['facts_08', '8. 证据清单', ''],
      ['facts_09', '关联案件信息', ''],
    ],
    sbsqbhfs: [
      ['facts_01', '商标信息', ''],
      ['facts_02', '1. 诉争商标', '1. 申请人：原告\n2. 申请号：\n3. 申请日期 年 月 日\n4. 标志：（浮于文字上方，居中，纵横比与商标局网站查询图样一致，宽度 5cm）\n5. 指定使用商品 / 服务（第 类，类似群 ）：'],
      ['facts_03', '2. 引证商标（如有多个 引证商标，逐一列明）', '（一）引证商标 ：\n1. 注册人：\n2. 注册号：\n3. 申请日期 年 月 日\n4. 初审公告日期 年 月 日（若涉及商标法三十一条案件请注明 此项）\n5. 专用权期限至： 年 月 日\n6. 标志：（浮于文字上方，居中，纵横比与商标局网站查询图样一致，宽度 5cm） 7. 核定使用商品 / 服务（第 类，类似群 ）： 商标状态（如撤销复审中、无效宣告程序中等，行政诉讼中，无变化的填 “无变化”）：\n（二）引证商标 ：（格式同上）'],
      ['facts_04', '其他需要确认的事实', ''],
      ['facts_05', '1. 对诉争商标指定使用 的复审商品 / 服务与各 引证商标核定使用商 品 / 服务构成类似商品 / 服务是否有异议', '无异议□ 有异议□\n简要理由：'],
      ['facts_06', '2. 对诉争商标与各引证 商标标志构成近似是 否有异议', '无异议□ 有异议□\n简要理由：'],
      ['facts_07', '3. 引证商标的权利变化 情况', '无此种情况□ 有此种情况□\n引证商标权利变化，是否对裁判结果有影响：是□ / 否□ 具体对商品类似、商标近似的影响： 简要说明：\n【引 证 商 标 已 被 宣 告 无 效 】 引 证 商 标 于 年 月 日 在 全 部 / 部 分 商 品 / 服 务 上 的 注 册 均 已 被 宣 告 无 效（第 期 商 标 公 告， 年 月 日）。\n【引证商标已被撤销】引证商标 因注册商标连续三年不使用在全部 / 部分核定使用商品 / 服务上的注册被撤销并已公告（第 期商标公 告， 年 月 日）。\n【引证商标未续展】引证商标 因专用权期限届满未续展，已丧失商标专 用权，不再构成诉争商标申请注册的权利障碍。\n【引证商标权利人注销】引证商标 权利人 已于 年 月 日\n被注销。（需提交引证商标权利人注销的相关工商档案材料）。\n【引证商标被转让】引证商标于 年 月 日经核准由 转让于\n（第 期商标公告， 年 月 日）。\n其他：'],
      ['facts_08', '4. 是否有其他需要说明 的事实', '无此种情况□ 有此种情况□\n简要说明：\n1.【原告名称变更】原告名称于 年 月 日经核准由“ ”\n变更为“ ”。\n2.【诉争商标转让】诉争商标于 年 月 日经核准由 转让于\n（第 期商标公告， 年 月 日）。\n3.【原告公司存续情况】 年 月 日经查询，原告公司是否存续\n（若注销，请填写注销时间及注销原因）。\n4.【指导性案例、人民法院案例库案例等权利】 年 月 日， 法\n院作出的 号判决书 / 裁定书。'],
      ['facts_09', '5. 与本案有关联的案件 情况', '无此种情况□ 有此种情况□\n□关联行政案件未作出决定：商标号 / 申请号、无效宣告请求人、国家知识 产权局案件编号\n□关联行政案件已作出决定：商标号 / 申请号、无效宣告请求人、国家知识 产权决定号、决定结论、是否生效\n□关联行政案件已进入诉讼程序：案号、承办人、商标号 / 申请号、案件结 果、是否已生效\n□关联民事案件：受理法院、案号、联系方式、各方当事人名称、商标号、 商标名称、商标权人、原告诉求、案件状态、裁判文书\n以上均可详细描述案件情况，若有相关文书需以附件形式提交相关文本'],
      ['facts_10', '6. 与本案相关的程序 问题', '1. 对作出被诉决定的行政程序是否有异议？否□ 是□ 请说明理由\n2. 本案是否同意适用简易程序审理？\n□同意本案适用简易程序审理，本案不申请审前化解 / 申请审前化解（若同 意简易程序审理，可进一步申请审前化解，符合申请审前化解的案件需为 引证商标预计在 3 个月内被公告无效、撤销、转让，或引证商标因专用权 期限届满并在 3 个月内将过宽展期的案件，申请审前化解请以起诉状附件 形式一并提交初步证明材料，附件形式请参考下述示例。同意适用简易程 序且经审查符合审前化解条件的案件可暂缓审理 3 个月）\n□不同意本案适用简易程序审理\n理由（需于提交起诉书之日起五日内，向本院指定邮箱提交书面异议。期 限内未提出异议的，本院可以按照简易程序进行审理。邮箱：jzys@bjcourt. gov.cn）'],
    ],
    sbcxfs: [
      ['facts_01', '1. 原告主体情况', '诉讼提起主体：诉争商标权利人□\n诉争商标撤销申请人 □ 其他□ 具体：'],
      ['facts_02', '2. 主张撤销被诉决定的 理由', '注册商标成为其复审商品 / 服务的通用名称。□ 有正当理由三年不使用。□\n诉争商标在全部复审商品 / 服务上进行了使用。□ 诉争商标在部分复审商品 / 服务上进行了使用。□\n不足以证明诉争商标在复审商品 / 服务上进行了使用。□ 其他□ 具体：'],
      ['facts_03', '3. 行政程序中提交的证 据', ''],
      ['facts_04', '4. 一审阶段是否有新证 据（行政程序中未提 交过的证据）', '是□ 证据类型：□书证 份\n□物证 份\n□视听资料 份\n□电子证据 份\n□证人证言 份 □其他 份\n行政程序中未提交上述证据的客观理由：\n否□'],
      ['facts_05', '5. 证据清单', ''],
      ['facts_06', '6. 其他需要说明的内容', ''],
      ['facts_07', '诉争商标及其权利人的变化情况', ''],
      ['facts_08', '诉争商标转让□', '诉争商标于 20 年 月 日经核准由 转让于 （第 期商标公\n告，20 年 月 日）'],
      ['facts_09', '诉争商标已被无效 / 被 撤销 / 被注销□', '诉争商标于 20 年 月 日在全部 / 部分商品或服务（请列明具体 商品或服务名称及类似群组）上的注册均已被宣告无效 / 被撤销 / 被注销 （第 期商标公告，20 年 月 日）。'],
      ['facts_10', '诉争商标未续展□', '诉争商标因专用权期限届满未续展。'],
      ['facts_11', '诉争商标权利人注销 / 名义 / 名称变更□', '诉争商标权利人已于 20 年 月 日被注销 / 诉争商标权利人名义 （或名称）于 20 年 月 日变更为 。（注销及名称变更的需提供 相关工商档案材料或变更后的主体证明材料）'],
      ['facts_12', '关联案件信息', ''],
      ['facts_13', '诉争商标是否处在其 他评审程序（包括但 不限于无效宣告、撤 销及撤销复审程序） 或行政诉讼程序中', '□相关评审程序未作出裁决\n评审程序申请人： 国家知识产权局案件编号： □相关评审程序已经作出裁决尚未进入诉讼\n国家知识产权局裁定 / 决定号： 裁定 / 决定结论：\n决定文本（如有单独提交）\n□相关评审程序已经作出裁决且已经进入诉讼\n国家知识产权局裁定 / 决定号： 裁定 / 决定结论：\n决定文本（如有单独提交）\n受理法院： 案号： 联系方式：\n案件状态： 裁判文书（如有单独提交） □否'],
      ['facts_14', '诉争商标是否处其他 民事诉讼程序中', '□是 受理法院： 案号： 联系方式：\n各方当事人名称：\n商标号： 商标名称： 商标权人：\n原告诉求： 案件状态：\n裁判文书（如有单独提交） □否'],
      ['facts_15', '指导性案例、人民法院案例库案例等情况', ''],
      ['facts_16', '具体案件情况', '20 年 月 日， 法院 案号 行政 / 民事判决 / 裁定书（如\n有单独提交）'],
      ['facts_17', '4. 其他证据', ''],
    ],
    sbwx: [
      ['facts_01', '1. 原告主体情况', '诉讼提起主体：诉争商标权利人□\n诉争商标无效宣告请求人 □ 涉案商标信息：诉争商标信息： 是否有引证商标：是□,引证商标信息： 否□\n其他□ 具体：'],
      ['facts_02', '2. 诉争商标信息', '注册人：原告 / 第三人 注册号：\n申请日期： 年 月 日\n专用权期限至： 年 月 日\n标志：\n核定使用商品 / 服务（第 类，类似群 ）：'],
      ['facts_03', '3. 引证商标信息（如有）', '是否有引证商标： 是□\n引证商标（多个引证商标逐一列明） 注册人 / 申请人：原告 / 第三人\n注册号 / 申请号：××\n申请日期： 年 月 日\n初审公告日期： 年 月 日（若涉及商标法三十一条案件请注明此项）\n专用权期限至： 年 月 日\n标志：\n核定 / 指定使用商品 / 服务（第 类，类似群 ）：（具体商品或服务\n名称，需列全） 否□'],
      ['facts_04', '4. 事实及理由详述（可 另附页）', ''],
      ['facts_05', '5. 需要确认的其他事实', '（1）对诉争商标核定使用的商品 / 服务与各引证商标核定使用商品 / 服务构 成相同或类似商品 / 服务是否有异议？\n□无异议\n□有异议，简要理由：\n（2）对诉争商标与各引证商标标志构成相同或近似是否有异议？ □无异议\n□有异议，简要理由：\n（3）诉争商标及其权利人的变化情况：\n□诉争商标转让：诉争商标于 20 年 月 日经核准由 转让 于 （第 期商标公告，20 年 月 日）\n□诉争商标已被无效 / 被撤销 / 被注销：诉争商标于 20 年 月 日 在全部 / 部分商品或服务（请列明具体商品或服务名称及类似群 组）上的注册均已被宣告无效 / 被撤销 / 被注销（第 期商标公告， 20 年 月 日）。\n□诉争商标未续展：诉争商标因专用权期限届满未续展。\n□诉争商标权利人注销 / 名义 / 名称变更：诉争商标权利人已于 20 年 月 日被注销 / 诉争商标权利人名义（或名称）于 20 年 月 日变更为 。（注销及名称变更的需提供相关工商档 案材料或变更后的主体证明材料）\n□无\n（4）引证商标及其权利人的变化情况：\n□引证商标转让：引证商标（商标号 / 申请号： ）于 2 年 月 日 经核准由 转让于 （第 期商标公告，20 年 月 日）\n□引证商标已被无效 / 被撤销 / 被注销：引证商标（商标号 / 申请号： ） 于 20 年 月 日在全部 / 部分商品或服务（请列明具体商品或服 '],
      ['facts_06', '7. 一审阶段是否有新证 据提交（行政程序中未 提交过的证据）', '是□ 证据类型：□书证 份\n□物证 份\n□视听资料 份\n□电子证据 份\n□证人证言 份 □其他 份\n行政程序中未提交上述证据的客观理由：\n否□'],
      ['facts_07', '8. 证据清单', ''],
      ['facts_08', '9. 其他需要说明的内容', ''],
      ['facts_09', '关联案件信息', ''],
      ['facts_10', '诉争商标是否处在其他 评审程序（包括但不限 于无效宣告、撤销及撤 销复审程序）或行政诉 讼程序中', '□相关评审程序未作出裁决\n评审程序申请人： 国家知识产权局案件编号： □相关评审程序已经作出裁决尚未进入诉讼\n国家知识产权局裁定 / 决定号： 裁定 / 决定结论：\n决定文本（如有单独提交）\n□相关评审程序已经作出裁决且已经进入诉讼\n国家知识产权局裁定 / 决定号： 裁定 / 决定结论：\n决定文本（如有单独提交）\n受理法院： 案号： 联系方式：\n案件状态： 裁判文书（如有单独提交） □否'],
      ['facts_11', '诉争商标是否处其他民 事诉讼程序中', '□是 受理法院： 案号： 联系方式：\n各方当事人名称：\n商标号： 商标名称： 商标权人：\n原告诉求： 案件状态：\n裁判文书（如有单独提交） □否'],
      ['facts_12', '引证商标是否处在其他 评审程序（包括但不限 于无效宣告、撤销及撤 销复审程序）或行政诉 讼程序中', '□相关评审程序未作出裁决\n商标号 / 申请号： 商标名称： 商标权人 / 申请人：\n评审程序申请人： 国家知识产权局案件编号：\n□相关评审程序已经作出裁决尚未进入诉讼\n商标号 / 申请号： 商标名称： 商标权人 / 申请人：\n国家知识产权局裁定 / 决定号： 裁定 / 决定结论：\n决定文本（如有单独提交）\n□相关评审程序已经作出裁决且已经进入诉讼\n国家知识产权局裁定 / 决定号： 裁定 / 决定结论：\n决定文本（如有单独提交）\n受理法院： 案号： 联系方式：\n案件状态： 裁判文书（如有单独提交） □否'],
      ['facts_13', '引证商标是否处其他民 事诉讼程序中', '□是 受理法院： 案号： 联系方式：\n各方当事人名称：\n商标号： 商标名称： 商标权人：\n原告诉求： 案件状态：\n裁判文书（如有单独提交） □否'],
      ['facts_14', '指导性案例、人民法院案例库案例等情况', ''],
      ['facts_15', '具体案件情况', '20 年 月 日， 法院 案号 行政 / 民事判决 / 裁定书（如\n有单独提交）'],
      ['facts_16', '1. 被诉裁定 / 决定及涉案商标信息相关证据', ''],
      ['facts_17', '4. 其他证据', ''],
    ],
    zlbhfs: [
      ['facts_01', '1. 权利基础状况', '申请号：\n专利名称：\n专利类型：发明专利□ 实用新型专利□ 外观设计专利□\n专利领域：机械□ 电学□ 通信□ 化学□ 医药生物□ 光电□\n材料□ 其他□ 专利申请人：\n专利申请日： 优先权日：\n审查基础：申请文本 /× 年 × 月 × 日提交的修改文本\n同族专利情况：同族专利涉及 × 国、× 地区的 × 件专利， × 件获得授权 并处于有效状态，× 件被驳回申请， … …（详见附件 2 同族专利信息表）'],
      ['facts_02', '2. 本案行政程序情况', '× 年 × 月 × 日，国家知识产权局经其原审查部门审查，决定驳回本 申请。主要理由包括：（一）……。（二） ……。国家知识产权局原审查部门 引用了如下证据：×- ×（对比文件 1）： ……。×- ×（对比文件 2）： … …。\n× 年 × 月 × 日，国家知识产权局作出被诉决定，认为： ……。国家 知识产权局据此决定： … …。\n（对被诉决定作出程序如有异议，请说明具体理由。）'],
      ['facts_03', '4. 其他', '有□ 主要事实与理由：\n无□'],
    ],
    zlwx: [
      ['facts_01', '1. 权利基础状况', '专利号：\n专利名称：\n专利类型：发明专利□ 实用新型专利□ 外观设计专利□\n专利领域：机械□ 电学□ 通信□ 化学□ 医药生物□ 光电□\n材料□ 其他□ 专利权人：\n专利申请日： 优先权日：\n授权公告日：\n审查基础：授权公告文本 /× 年 × 月 × 日提交的修改文本 关联确权行政程序：（概述确权行政程序情况）\n同族专利情况：同族专利涉及 × 国、× 地区的 × 件专利， × 件获得授权 并处于有效状态，× 件被驳回申请， … …（详见附件 2 同族专利信息表）'],
      ['facts_02', '2. 本案行政程序情况', '× 年 × 月 × 日， ×× 请求国家知识产权局宣告本专利权利要求 ×/ 全部无效。主要理由包括：（一） ……。（二） … …。\n×× 提交了如下证据：×- ×（对比文件 1）： ……。×-×（对比文件 2）： ……。\n针对 ×× 提出的无效宣告请求，专利权人 ×× 提交了如下证据： ×- ×（反证 1）： ……。× - ×（反证 2）： … …。\n× 年 × 月 × 日，国家知识产权局作出被诉决定，认为： ……。国家 知识产权局据此决定： … …。\n（对被诉决定作出程序如有异议，请说明具体理由。）'],
      ['facts_03', '4. 其他', '有□ 主要事实与理由：\n无□'],
    ],
    ldzxz: [
      ['facts_01', '1. 被诉行政行为情况', '× 年 × 月 × 日， ×× 市场监管局作出被诉决定，主要内容为：（一） ×× 存在以下违法行为： ……。（二） … …。\n据此， ×× 市场监管局依据反垄断法第 × 条第 × 款的规定决定：对 ×× 处以 ×× 元罚款， … …（见原告证据 ×- ×： … …）。'],
      ['facts_02', '2. 被诉决定相关认定', '相关市场界定有无错误\n垄断行为认定有无错误\n垄断行为认定有无错误'],
      ['facts_03', '3. 被诉决定程序', '违反法定程序□ 具体分析： 超越职权□ 具体分析：\n滥用职权□ 具体分析： 其他□ 具体分析：'],
      ['facts_04', '4. 被诉决定处罚', '鉴于涉案垄断行为不成立，原告不应受到行政处罚。即便涉案垄断行 为成立，涉案处罚的内容、履行方式 …… 存在明显不当。\n罚款□ 具体分析：\n没收违法所得□ 具体分析： 责令停产停业□ 具体分析： 其他□ 具体分析：'],
      ['facts_05', '5. 其他', '有□ 主要事实与理由：\n无□'],
    ],
    hjwr: [
      ['facts_01', '1. 环境污染民事公益诉 讼类型', '□大气污染\n□电子废物污染 □光污染'],
      ['facts_02', '2. 具体环境污染行为', ''],
      ['facts_03', '3. 造成损害事实或损害 重大风险情况', ''],
      ['facts_04', '4. 行为与损害结果之间 具有因果关系的相关 材料', ''],
      ['facts_05', '5. 诉讼请求依据的法 律、行政法规等规定', ''],
      ['facts_06', '6. 其他需要说明的内容', ''],
      ['facts_07', '7. 证据清单', '1. 社会组织主体资格材料\n2. 社会组织无违法记录声明\n3. 被告违反法律规定污染环境、破坏生态行为的证明材料\n4. 相关行政机关查处被告违法行为的材料\n5. 监测数据、检验报告、鉴定报告、评估报告等\n……'],
    ],
    stph: [
      ['facts_01', '1. 生态破坏类型', '□生物多样性破坏 □景观多样性破坏 □生态系统破坏\n□重点生态区域（国家公园、自然保护区、自然公园或河流湖泊等岸线区 域）内生态破坏 □其他'],
      ['facts_02', '2. 具体生态破坏行为', ''],
      ['facts_03', '3. 造成损害事实或损害 重大风险情况', ''],
      ['facts_04', '4. 行为与损害结果之间 具有因果关系的相关 材料', ''],
      ['facts_05', '5. 诉讼请求依据的法 律、行政法规等规定', ''],
      ['facts_06', '6. 其他需要说明的内容', ''],
      ['facts_07', '7. 证据清单', '1. 社会组织主体资格材料\n2. 社会组织无违法记录声明\n3. 被告违反法律规定污染环境、破坏生态行为的证明材料\n4. 相关行政机关查处被告违法行为的材料\n5. 监测数据、检验报告、鉴定报告、评估报告等\n……'],
    ],
    stsh: [
      ['facts_01', '1. 生态环境损害类型', '□环境污染 □生态破坏'],
      ['facts_02', '2. 具体行为', ''],
      ['facts_03', '3. 造成损害事实', ''],
      ['facts_04', '4. 行为与损害之间具有 因果关系的相关材料', ''],
      ['facts_05', '5. 磋商情况（可另附 页）', ''],
      ['facts_06', '6. 诉讼请求依据的法 律、行政法规等规定', ''],
      ['facts_07', '7. 其他需要说明的内容', ''],
      ['facts_08', '8. 证据清单', '1. 省级、市地级政府指定原告提起本案诉讼的材料\n2. 经磋商未达成一致或者无法进行磋商的证明材料\n3. 被告违反法律规定污染环境、破坏生态行为的证明材料\n4. 相关行政机关查处被告违法行为的材料\n5. 监测数据、检验报告、鉴定报告、评估报告等\n……'],
    ],
    gjpcsqs1: [
      ['facts_01', '1. 赔偿义务机关是否就 赔偿申请作出自赔决定', '是□ 决定书文号：\n决定书作出时间： 决定书结果： 否□'],
      ['facts_02', '2. 复议机关是否作出复 议决定', '是□ 复议决定文号：\n复议决定作出时间： 复议决定结果： 否□'],
      ['facts_03', '3. 申请赔偿的法律依据 和理由', ''],
      ['facts_04', '4. 其他需要说明的内容', ''],
      ['facts_05', '5. 有无同类案件裁判文 书或指导性案例（可 另附页）', '是□ 案号 / 案例名称： 否□'],
      ['facts_06', '6. 证据清单（可另附 页）', ''],
    ],
    gjpcsqs2: [
      ['facts_01', '1. 申请赔偿的法律依据 和理由', ''],
      ['facts_02', '2. 其他需要说明的内容', ''],
      ['facts_03', '3. 有无同类案件裁判文书或指导性案例', '是□ 案号 / 案例名称：\n否□'],
      ['facts_04', '4. 证据清单（可另附 页）', ''],
    ],
    gjpcsqs3: [
      ['facts_01', '1. 赔偿义务机关是否就 赔偿申请作出自赔决定', '是□ 决定书文号：\n决定书作出时间： 决定书结果： 否□'],
      ['facts_02', '2. 复议机关是否作出复 议决定', '是□ 复议决定文号：\n复议决定作出时间： 复议决定结果 否□'],
      ['facts_03', '3. 申请赔偿的法律依据 和理由', ''],
      ['facts_04', '4. 有无伤情 / 死亡鉴定', '有□\n关于义务机关监管行为和伤亡结果之间的关系，鉴定结果是否对此作出 结论：是□ 否□ 无□'],
      ['facts_05', '5. 其他需要说明的内容', ''],
      ['facts_06', '6. 有无同类案件裁判文 书或指导性案例（可另 附页）', '是□ 案号 / 案例名称： 否□'],
      ['facts_07', '7. 证据清单（可另附 页）', ''],
    ],
    gjpcsqs4: [
      ['facts_01', '1. 申请赔偿的法律依据 和理由', ''],
      ['facts_02', '2. 其他需要说明的内容', ''],
      ['facts_03', '3. 有无同类案件裁判文 书或指导性案例（可另 附页）', '是□ 案号 / 案例名称： 否□'],
      ['facts_04', '4. 证据清单（可另附 页）', ''],
    ],
    cbpz: [
      ['facts_01', '1. 请求依据', '合同约定： 法律规定：'],
      ['facts_02', '2. 碰撞船舶情况', '本船船名： 对方船船名：\n本船国籍： 对方船国籍：\n本船所有人： 对方船所有人：'],
      ['facts_03', '3. 责任认定情况', '有□（调查机关、责任主体及责任大小等） 无□'],
      ['facts_04', '4. 有无填写《海事事故 调查表》', '有□ 无□'],
      ['facts_05', '5. 船舶价值', '元'],
      ['facts_06', '6. 船舶修理情况', '有□ 修船地点： 修理项目：\n应付修船费用： 元 已实际支付修船费用： 元\n无□'],
      ['facts_07', '7. 其他损失的依据', '有□ 依据名称：\n无□'],
      ['facts_08', '8. 其他需要说明的内容 （如海上保险合同赔偿 金支付凭证、权益转 让书、非本表列明损 失的法律依据等，可 另附页）', '有□ 无□'],
      ['facts_09', '9. 证据清单', ''],
    ],
    hsrs: [
      ['facts_01', '1. 请求依据', '合同约定： 法律规定：'],
      ['facts_02', '2. 船舶情况', '船名： 船舶所有人：'],
      ['facts_03', '3. 劳务关系情况', '雇主姓名： 工资标准：\n上船时间： 下船时间：'],
      ['facts_04', '4. 事故情况', '死亡□ 失踪□ 无伤残等级□ 有伤残等级□ 级\n事故调查机关：\n事故原因：船上劳务□ 船上劳务相关活动□ 其他'],
      ['facts_05', '5. 船舶、船员投保情况', ''],
      ['facts_06', '6. 其他情况', ''],
      ['facts_07', '7. 证据清单', ''],
    ],
    hshyd: [
      ['facts_01', '1. 请求依据', '合同约定： 法律规定：'],
      ['facts_02', '2. 合同签订情况', '（名称、编号、签订时间、地点等）'],
      ['facts_03', '3. 签订主体', '委托人： 受托人：'],
      ['facts_04', '4. 有关费用情况', '约定应收金额： 实际收到金额：'],
      ['facts_05', '5. 付款期限', '是否到期：是□ 否□\n约定付款期限： 年 月 日'],
      ['facts_06', '6. 委托事项内容', '订舱□ 拖车□ 报关□\n其他事项：'],
      ['facts_07', '7. 委托事项完成情况', '已完成□\n未完成□ 原因：'],
      ['facts_08', '8. 是否完成费用对账', '已完成□\n未完成□ 原因：'],
      ['facts_09', '9. 是否已开具费用发票', '是□ 否□'],
      ['facts_10', '10. 其他需要说明的内 容', ''],
      ['facts_11', '11. 证据清单（可另附 页）', ''],
    ],
    cylw: [
      ['facts_01', '1. 诉请依据', '合同约定：\n法律规定：（法律及司法解释的规定，要写明具体条文）'],
      ['facts_02', '2. 合同签订情况', '（名称、签订主体、时间、约定工资及报酬等）'],
      ['facts_03', '3. 合同履行情况', '（包括船名、船舶所有人名称或姓名、雇主姓名、上船时间、下船时间、 工作内容、回港时间、地点、实际领取工资及报酬等）'],
      ['facts_04', '4. 仲裁相关情况', '（申请仲裁时间、仲裁请求、仲裁文书、仲裁结果等）'],
      ['facts_05', '5. 其他情况', ''],
      ['facts_06', '6. 证据清单', ''],
    ],
  };
  const GENERAL = [
    ['facts_01', '1. 基本事实（合同/法律关系建立情况）', ''],
    ['facts_02', '2. 合同/法律关系履行情况', ''],
    ['facts_03', '3. 违约/侵权/损害情况', ''],
    ['facts_04', '4. 损失金额及计算方式', ''],
    ['facts_05', '5. 担保情况（如有）', ''],
    ['facts_06', '6. 其他需要说明的内容（可另附页）', ''],
    ['facts_07', '7. 请求依据（合同约定/法律规定）', ''],
    ['facts_08', '8. 证据清单（可另附页）', ''],
  ];
  return FACTS[typeId] || GENERAL;
}


function buildJurisdictionSection() {
  const j = state.data.jurisdiction || {};
  const setVal = (id, val) => { const el = document.getElementById(id); if (el && val) el.value = val; };
  if (j.court) {
    setVal('j-court', j.court);
  } else {
    const courtEl = document.getElementById('court');
    if (courtEl && courtEl.value) setVal('j-court', courtEl.value);
  }
  setVal('j-basis', j.basis);
  const dateEl = document.getElementById('j-date');
  if (dateEl) dateEl.value = j.date || new Date().toISOString().split('T')[0];
  // Set mediation radio
  const med = j.mediation || 'no';
  const medEl = document.querySelector(`input[name="mediation"][value="${med}"]`);
  if (medEl) medEl.checked = true;
}

function updateBadges() {
  document.getElementById('badge-plaintiffs').textContent = state.data.plaintiffs.length;
  document.getElementById('badge-defendants').textContent = state.data.defendants.length;
  document.getElementById('badge-thirds').textContent = state.data.thirds.length;
}

// ============================================================
// Party interactions
// ============================================================
function showPartySection(name) {
  document.querySelectorAll('.party-section').forEach(s => s.classList.remove('visible'));
  document.querySelectorAll('.party-tab').forEach(t => t.classList.remove('active'));
  document.getElementById('section-' + name).classList.add('visible');
  document.getElementById('tab-' + name).classList.add('active');
}

function saveField(role, index, field, value) {
  if (state.data[role] && state.data[role][index]) {
    state.data[role][index][field] = value;
  }
}

function togglePartyType(role, index, type) {
  if (state.data[role][index]) {
    state.data[role][index].type = type;
    buildPartySection(role);
  }
}

function addParty(role, type) {
  state.data[role].push({type, name:'', _id:uid()});
  buildPartySection(role);
  updateBadges();
  showToast('已添加' + {plaintiffs:'原告',defendants:'被告',thirds:'第三人'}[role] + '表格', 'success');
}

function removeParty(role, index) {
  state.data[role].splice(index, 1);
  buildPartySection(role);
  updateBadges();
}

function toggleAgent() {
  const has = document.getElementById('agent-yes').checked;
  document.getElementById('agent-fields').style.display = has ? 'block' : 'none';
}

// ============================================================
// Preview generation
// ============================================================
function generatePreview() {
  // Sync data from form before preview
  syncFormData();

  const ctn = document.getElementById('preview-content');
  ctn.innerHTML = buildDocHtml();

  // Set default export filename
  const today = new Date().toISOString().slice(0,10).replace(/-/g,'');
  const meta = getCurrentTemplateMeta();
  const fnEl = document.getElementById('export-filename'); if (fnEl) fnEl.value = `${meta.title.replace(/[（）()]/g,'-').replace(/-+/g,'-')}-${today}`;
  updateTemplateMetaCard();
}

function syncFormData() {
  // Sync party fields
  ['plaintiffs','defendants','thirds'].forEach(role => {
    state.data[role].forEach((p, i) => {
      const fields = p.type === 'person'
        ? ['name','gender','birth','nation','idType','idNum','addr','habitual','phone','work','job']
        : ['name','addr','regAddr','legalRep','job','phone','creditCode','orgType','ownership'];
      fields.forEach(f => {
        const el = document.getElementById(`${role}_${i}_${f}`);
        if (el) p[f] = el.value;
      });
    });
  });

  // Agent
  const g = id => document.getElementById(id);
  state.data.agent = {
    has: g('agent-yes')?.checked || false,
    name: g('agent-name')?.value || '',
    job: g('agent-job')?.value || '',
    firm: g('agent-firm')?.value || '',
    phone: g('agent-phone')?.value || '',
    auth: g('auth-special')?.checked ? 'special' : 'general'
  };

  // Claims - sync dynamic claim fields + fixed fields
  const claimData2 = {
    full: '',
    total: document.getElementById('claim-total')?.value || '',
    lawyerFee: document.getElementById('claim-lawyer-fee')?.value || '',
    preservation: document.getElementById('claim-preservation')?.value || '',
    other: document.getElementById('claim-other')?.value || '',
  };
  getClaimFields(state.caseType).forEach(([key]) => {
    const el = document.getElementById('claim-field-' + key);
    if (el) claimData2[key] = el.value;
  });
  state.data.claims = claimData2;

  // Facts
  state.data.facts = {};
  document.querySelectorAll('[id^="fact-"]').forEach(el => {
    const key = el.id.replace('fact-','');
    state.data.facts[key] = el.value;
  });
  const evEl = document.getElementById('evidence-list'); if (evEl) state.data.facts.evidence = evEl.value;

  // Jurisdiction
  state.data.jurisdiction = {
    court: document.getElementById('j-court')?.value || '',
    basis: document.getElementById('j-basis')?.value || '',
    date: document.getElementById('j-date')?.value || '',
    notes: document.getElementById('j-notes')?.value || '',
    mediation: document.querySelector('input[name="mediation"]:checked')?.value || 'no'
  };
}

function buildDocHtml() {
  const d = state.data;
  const today = d.jurisdiction?.date || new Date().toLocaleDateString('zh-CN');
  const meta = getCurrentTemplateMeta();
  const validationErrors = validateTemplateCompleteness();
  let html = `
    <div class="preview-lock-note">${meta.lockTip}<br>当前套用范本：${meta.source}</div>
    ${validationErrors.length ? `<div class="preview-validation">预检提示：${validationErrors.join('；')}。</div>` : ''}
    <div class="doc-title">${meta.kind || '起诉状'}</div>
    <div style="text-align:center;font-size:16px;margin-bottom:6px;">${meta.title.replace(/^(民事起诉状|行政起诉状|刑事（附带民事）自诉状|强制执行申请书|国家赔偿申请书|.*申请书)/,'').trim() || `（${state.caseTypeName||'民事纠纷'}）`}</div>
    <div style="text-align:center;font-size:13px;color:#555;margin-bottom:24px;">${d.jurisdiction?.court||'　　　　法院'}　　收</div>
  `;

  function orgTypeStr(t) {
    const types = ['有限责任公司','股份有限公司','上市公司','其他企业法人','事业单位','社会团体','基金会','个人独资企业','合伙企业'];
    return types.map(tp => tp+(tp===t?'☑':'□')).join('  ');
  }
  function ownerStr(o) {
    if (!o) return '国有□（控股□  参股□）  民营□  其他□';
    if (o.includes('国有')||o.includes('控股')) return '国有☑（控股'+(o.includes('控股')?'☑':'□')+'  参股'+(o.includes('参股')?'☑':'□')+'）  民营□  其他□';
    if (o.includes('民营')) return '国有□（控股□  参股□）  民营☑  其他□';
    return '国有□（控股□  参股□）  民营□  其他☑';
  }

  function partyInlineHtml(p) {
    if (p.type === 'person') {
      const gStr = p.gender==='男' ? '男☑  女□' : p.gender==='女' ? '男□  女☑' : '男□  女□';
      return [
        '姓名：'+(p.name||''),
        '性别：'+gStr,
        '出生日期：'+(p.birth||'　　年　月　日')+'    民族：'+(p.nation||''),
        '工作单位：'+(p.work||'')+'      职务：'+(p.job||'')+'      联系电话：'+(p.phone||''),
        '住所地（户籍所在地）：'+(p.addr||''),
        '经常居住地：'+(p.habitual||''),
        '证件类型：'+(p.idType||'居民身份证'),
        '证件号码：'+(p.idNum||''),
      ].join('<br>');
    } else {
      return [
        '名称：'+(p.name||''),
        '住所地（主要办事机构所在地）：'+(p.addr||''),
        '注册地/登记地：'+(p.regAddr||''),
        '法定代表人/负责人：'+(p.legalRep||'')+'      职务：'+(p.job||'')+'      联系电话：'+(p.phone||''),
        '统一社会信用代码：'+(p.creditCode||''),
        '类型：'+orgTypeStr(p.orgType),
        '所有制性质：'+ownerStr(p.ownership),
      ].join('<br>');
    }
  }

  // 当事人信息大表
  html += '<table class="doc-table" style="margin-bottom:0;"><thead><tr><th colspan="2" style="background:#D9E2F3;">当事人信息</th></tr></thead><tbody>';

  d.plaintiffs.forEach((p, i) => {
    const num = d.plaintiffs.length > 1 ? i+1 : '';
    const typeLabel = p.type==='org' ? '（法人、非法人组织）' : '（自然人）';
    html += `<tr><td style="width:28%;background:#fff;font-size:13px;vertical-align:middle;text-align:left;">原告${num}<br>${typeLabel}</td><td style="font-size:13px;line-height:1.8;text-align:left;">${partyInlineHtml(p)}</td></tr>`;
  });

  if (d.agent?.has || d.agent?.name) {
    const authStr = d.agent?.auth==='special' ? '一般授权□    特别授权☑' : '一般授权☑    特别授权□';
    const agentContent = [
      '有☑    无□',
      '姓名：'+(d.agent?.name||'')+'      职务：'+(d.agent?.job||''),
      '单位：'+(d.agent?.firm||'')+'      联系电话：'+(d.agent?.phone||''),
      '代理权限：'+authStr,
    ].join('<br>');
    html += `<tr><td style="background:#fff;font-size:13px;vertical-align:middle;text-align:left;">委托诉讼代理人</td><td style="font-size:13px;line-height:1.8;text-align:left;">${agentContent}</td></tr>`;
  }

  d.defendants.forEach((p, i) => {
    const num = d.defendants.length > 1 ? i+1 : '';
    const typeLabel = p.type==='org' ? '（法人、非法人组织）' : '（自然人）';
    html += `<tr><td style="width:28%;background:#fff;font-size:13px;vertical-align:middle;text-align:left;">被告${num}<br>${typeLabel}</td><td style="font-size:13px;line-height:1.8;text-align:left;">${partyInlineHtml(p)}</td></tr>`;
  });

  if (d.thirds && d.thirds.length) {
    d.thirds.forEach((p, i) => {
      const num = d.thirds.length > 1 ? i+1 : '';
      const typeLabel = p.type==='org' ? '（法人、非法人组织）' : '（自然人）';
      html += `<tr><td style="background:#fff;font-size:13px;vertical-align:middle;text-align:left;">第三人${num}<br>${typeLabel}</td><td style="font-size:13px;line-height:1.8;text-align:left;">${partyInlineHtml(p)}</td></tr>`;
    });
  }

  html += '</tbody></table>';

  // 诉讼请求/申请事项表
  html += `<table class="doc-table" style="margin-top:0;margin-bottom:0;border-top:0;"><thead><tr><th colspan="2" style="background:#D9E2F3;">${meta.requestHeader}</th></tr></thead><tbody>`;
  html += `<tr><td style="width:38%;background:#F2F2F2;font-size:12px;text-align:left;">（请严格按对应要素式范本栏目填写；仅填充内容，不改变原要素结构）</td><td></td></tr>`;
  const claimFields2 = getClaimFields(state.caseType);
  claimFields2.forEach(([key, label, hint]) => { label = label.replace(/^【.*?】/, '').trim();
    const cval2 = d.claims?.[key] || '';
    const ccell2 = cval2 ? esc(cval2) : esc(hint || '');
    html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;vertical-align:top;">${label}</td><td style="font-size:13px;text-align:left;white-space:pre-line;vertical-align:top;">${ccell2}</td></tr>`;
  });
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">是否主张诉讼费用</td><td style="font-size:13px;text-align:left;">${d.claims?.lawyerFee==='yes'?'是☑  否□':'是□  否☑'}</td></tr>`;
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">其他请求</td><td style="font-size:13px;text-align:left;">${esc(d.claims?.other||'')}</td></tr>`;
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">标的总额</td><td style="font-size:13px;text-align:left;">${esc(d.claims?.total||'')}</td></tr>`;
  html += '</tbody></table>';

  // 管辖约定
  html += '<table class="doc-table" style="margin-top:0;margin-bottom:0;border-top:0;"><thead><tr><th colspan="2" style="background:#D9E2F3;">约定管辖和诉前保全</th></tr></thead><tbody>';
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">1. 有无仲裁、法院管辖约定</td><td style="font-size:13px;text-align:left;">${d.jurisdiction?.basis?'有☑  无□<br>'+esc(d.jurisdiction.basis):'有□  无☑'}</td></tr>`;
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">2. 是否已经诉前保全</td><td style="font-size:13px;text-align:left;">${d.claims?.preservation==='yes'?'是☑  否□':'是□  否☑'}</td></tr>`;
  html += '</tbody></table>';

  // 事实与理由表
  html += '<table class="doc-table" style="margin-top:0;margin-bottom:0;border-top:0;"><thead><tr><th colspan="2" style="background:#D9E2F3;">事实与理由</th></tr></thead><tbody>';
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">（可完整表述纠纷涉及的事实与理由；为方便、准确梳理要点，相关内容请在下方要素式表格中填写）</td><td></td></tr>`;
  const factsFields2 = getFactsFields(state.caseType);
  factsFields2.forEach(([key, label, hint]) => {
    const displayLabel = label.replace(/^【.*?】/, '').trim();
    const val = d.facts?.[key] || '';
    // 有AI值直接显示；无AI值则显示hint格式模板供律师填写
    const cellContent = val ? esc(val) : esc(hint || '');
    html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;vertical-align:top;">${displayLabel}</td><td style="white-space:pre-line;font-size:13px;text-align:left;vertical-align:top;">${cellContent}</td></tr>`;
  });
  html += '</tbody></table>';

  // 调解意愿（完整三行）
  html += '<table class="doc-table" style="margin-top:0;margin-bottom:0;border-top:0;"><thead><tr><th colspan="2" style="background:#D9E2F3;">对纠纷解决方式的意愿</th></tr></thead><tbody>';
  html += `<tr><td style="background:#F2F2F2;font-size:12px;width:28%;text-align:left;">是否了解调解作为非诉讼纠纷解决方式，能及时、高效、低成本、不伤和气地解决纠纷</td><td style="font-size:13px;text-align:left;">了解☑　　不了解□</td></tr>`;
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">是否了解先行调解解决纠纷的好处</td><td style="font-size:12px;line-height:1.9;text-align:left;">1. 立案后选择先行调解的，可以很快启动调解程序。如不同意调解，法院将依程序开庭审理案件，但可能需要经过较长一段时间的排期等待，且审理、执行周期相对较长。<br>了解☑　　不了解□<br>2. 选择先行调解，调解成功且自动履行的免交诉讼费用，申请司法确认的不交纳诉讼费用，要求出具调解书的减半交纳诉讼费用。<br>了解☑　　不了解□<br>3. 首次调解不成功，但仍有继续调解意愿的，可以选择更换调解组织和调解员再进行调解。调解无法达成一致意见的，法院将依程序排期开庭。<br>了解☑　　不了解□<br>4. 依照法律规定，调解具有保密性要求，调解过程不公开，调解协议未经当事人同意不得公开。<br>了解☑　　不了解□<br>5. 调解达成的协议具有法律效力，可以依照法律规定申请司法确认，具有强制执行效力。<br>了解☑　　不了解□</td></tr>`;
  const medYes = d.jurisdiction?.mediation==='yes';
  html += `<tr><td style="background:#F2F2F2;font-size:12px;text-align:left;">是否考虑先行调解</td><td style="font-size:13px;line-height:2;text-align:left;">${medYes?'是☑':'是□'}<br>${!medYes?'否☑':'否□'}<br>暂不确定，想要了解更多内容□</td></tr>`;
  html += '</tbody></table>';

  // 签名
  html += `<div style="text-align:right;margin-top:32px;font-size:13px;line-height:2.4;">
    <div>具状人（签字、盖章）：</div>
    <div>日期：${today}</div>
  </div>`;

  return html;
}


// ============================================================
// Export DOCX
// ============================================================
async function exportDocx() {
  syncFormData();
  const D = window.docx;
  if (!D) { showToast('DOCX 库未加载，请检查网络后刷新页面', 'error'); return; }
  showToast('正在生成 DOCX 文件…');

  try {
    const { Document, Packer, Paragraph, Table, TableRow, TableCell, TextRun,
            AlignmentType, WidthType, ShadingType, BorderStyle, VerticalAlign } = D;

    const d = state.data;

    // ── Page / table dimensions ──
    const PAGE_W = 8640; // 12240 - 1800*2 margins
    const LEFT_P = 2551, RIGHT_P = PAGE_W - LEFT_P;
    const LEFT_D = 3402, RIGHT_D = PAGE_W - LEFT_D;
    const BDR = { style: BorderStyle.SINGLE, size: 4, color: '000000', space: 0 };
    const BORDERS = { top: BDR, bottom: BDR, left: BDR, right: BDR };

    // ── Text runs ──
    function r(text, opts = {}) {
      return new TextRun({ text: String(text||''), bold: !!opts.bold, size: opts.size||21,
        font: { name: opts.font||'宋体', eastAsia: opts.font||'宋体', ascii: opts.font||'宋体' } });
    }
    function br() { return new TextRun({ break: 1 }); }
    function sp(bef, aft) { return { before: bef||20, after: aft||20, line: 240, lineRule: 'auto' }; }
    function para(runs, align) {
      return new Paragraph({ spacing: sp(), alignment: align||AlignmentType.LEFT, children: runs });
    }

    // ── Cells ──
    function headerRow(text, totalW) {
      return new TableRow({ children: [new TableCell({
        borders: BORDERS, columnSpan: 2,
        width: { size: totalW, type: WidthType.DXA },
        shading: { fill: 'D9E2F3', type: ShadingType.CLEAR, color: 'D9E2F3' },
        margins: { top: 60, bottom: 60, left: 120, right: 120 },
        children: [new Paragraph({ alignment: AlignmentType.CENTER, spacing: sp(),
          children: [r(text, { bold: true, size: 22 })] })]
      })] });
    }

    function labelCell(text, w) {
      return new TableCell({
        borders: BORDERS, width: { size: w, type: WidthType.DXA },
        shading: { fill: 'F2F2F2', type: ShadingType.CLEAR, color: 'F2F2F2' },
        margins: { top: 60, bottom: 60, left: 120, right: 120 },
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({ spacing: sp(), alignment: AlignmentType.LEFT, children: [r(text, { size: 19 })] })]
      });
    }

    function valueCell(runs, w) {
      return new TableCell({
        borders: BORDERS, width: { size: w, type: WidthType.DXA },
        margins: { top: 60, bottom: 60, left: 120, right: 120 },
        children: [new Paragraph({ spacing: sp(), alignment: AlignmentType.LEFT, children: runs })]
      });
    }

    function dataRow(label, value) {
      const lines = String(value||'').split('\n');
      const runs = [];
      lines.forEach((ln, i) => { if(i>0) runs.push(br()); runs.push(r(ln)); });
      return new TableRow({ children: [labelCell(label, LEFT_D), valueCell(runs.length?runs:[r('')], RIGHT_D)] });
    }

    // ── Party row (left=role, right=all fields inline) ──
    function orgTypeStr(t) {
      const types = ['有限责任公司','股份有限公司','上市公司','其他企业法人','事业单位','社会团体','基金会','社会服务机构','机关法人','农村集体经济组织法人','城镇农村的合作经济组织法人','基层群众性自治组织法人','个人独资企业','合伙企业','不具有法人资格的专业服务机构'];
      return types.map(tp => tp + (tp===t?'☑':'□')).join('  ');
    }
    function ownerStr(o) {
      if (!o) return '国有□（控股□  参股□）  民营□  其他□';
      if (o.includes('国有')||o.includes('控股')||o.includes('参股')) {
        return '国有☑（控股'+(o.includes('控股')?'☑':'□')+'  参股'+(o.includes('参股')?'☑':'□')+'）  民营□  其他□';
      }
      if (o.includes('民营')) return '国有□（控股□  参股□）  民营☑  其他□';
      return '国有□（控股□  参股□）  民营□  其他☑';
    }

    function partyRow(roleLabel, typeLabel, p) {
      const leftRuns = [r(roleLabel), br(), r(typeLabel)];
      const rightRuns = [];
      if (p.type === 'person') {
        const gStr = p.gender==='男' ? '男☑  女□' : p.gender==='女' ? '男□  女☑' : '男□  女□';
        rightRuns.push(
          r('姓名：'+(p.name||'')), br(),
          r('性别：'+gStr), br(),
          r('出生日期：'+(p.birth||'　　年　月　日')+'    民族：'+(p.nation||'')), br(),
          r('工作单位：'+(p.work||'')+'      职务：'+(p.job||'')+'      联系电话：'+(p.phone||'')), br(),
          r('住所地（户籍所在地）：'+(p.addr||'')), br(),
          r('经常居住地：'+(p.habitual||'')), br(),
          r('证件类型：'+(p.idType||'居民身份证')), br(),
          r('证件号码：'+(p.idNum||''))
        );
      } else {
        rightRuns.push(
          r('名称：'+(p.name||'')), br(),
          r('住所地（主要办事机构所在地）：'+(p.addr||'')), br(),
          r('注册地/登记地：'+(p.regAddr||'')), br(),
          r('法定代表人/负责人：'+(p.legalRep||'')+'      职务：'+(p.job||'')+'      联系电话：'+(p.phone||'')), br(),
          r('统一社会信用代码：'+(p.creditCode||'')), br(),
          r('类型：'+orgTypeStr(p.orgType)), br(),
          r('所有制性质：'+ownerStr(p.ownership))
        );
      }
      return new TableRow({ children: [
        new TableCell({
          borders: BORDERS, width: { size: LEFT_P, type: WidthType.DXA },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ spacing: sp(), alignment: AlignmentType.LEFT, children: leftRuns })]
        }),
        valueCell(rightRuns, RIGHT_P)
      ]});
    }

    function agentRow(a) {
      const authStr = a.auth==='special' ? '一般授权□    特别授权☑' : '一般授权☑    特别授权□';
      const runs = [
        r('有'+(a.has?'☑':'□')+'    无'+(a.has?'□':'☑')), br(),
        r('姓名：'+(a.name||'')+'      职务：'+(a.job||'')), br(),
        r('单位：'+(a.firm||'')+'      联系电话：'+(a.phone||'')), br(),
        r('代理权限：'+authStr)
      ];
      return new TableRow({ children: [
        new TableCell({
          borders: BORDERS, width: { size: LEFT_P, type: WidthType.DXA },
          margins: { top: 60, bottom: 60, left: 120, right: 120 },
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({ spacing: sp(), alignment: AlignmentType.LEFT, children: [r('委托诉讼代理人')] })]
        }),
        valueCell(runs, RIGHT_P)
      ]});
    }

    // ── Build tables ──
    const docChildren = [];

    // Title
    docChildren.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 0, after: 40 },
      children: [new TextRun({ text: '民事起诉状', bold: true, size: 44,
        font: { name: '方正小标宋简体', eastAsia: '方正小标宋简体', ascii: '方正小标宋简体' } })]
    }));
    docChildren.push(new Paragraph({
      alignment: AlignmentType.CENTER, spacing: { before: 0, after: 120 },
      children: [r('（'+(state.caseTypeName||'民事纠纷')+'）', { size: 28 })]
    }));

    // Instructions
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing: sp(20,20), children: [r('说明：', {bold:true,size:18})] }));
    ['为了方便您更好地参加诉讼，保护您的合法权利，请填写本表。',
     '1. 起诉时需向人民法院提交证明您身份的材料，如身份证复印件、营业执照复印件等。',
     '2. 本表所列内容是您提起诉讼以及人民法院查明案件事实所需，请务必如实填写。',
     '3. 本表有些内容可能与您的案件无关，您认为与案件无关的项目可以填"无"或不填；对于本表中勾选项可以在对应项打"√"；您认为另有重要内容需要列明的，可以另附页填写。',
     '4. 本表word电子版填写时，相关栏目可复制粘贴或扩容，但不得改变要素内容、格式设置。例如，多原告、多被告或多委托诉讼代理人等情况，可根据实际情况复制粘贴。',
    ].forEach(t => docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing: sp(20,20), children: [r(t,{size:18})] })));
    docChildren.push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:sp(80,0), children:[r('★特别提示★',{bold:true,size:18})] }));
    docChildren.push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:sp(0,80), children:[r('诉讼参加人应遵守诚信原则如实认真填写表格。',{size:18})] }));
    docChildren.push(new Paragraph({ alignment:AlignmentType.CENTER, spacing:sp(0,120), children:[r('如果诉讼参加人违反有关规定，虚假诉讼、恶意诉讼、滥用诉权，人民法院将视违法情形依法追究责任。',{size:18})] }));
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing: { before:0, after:0 } }));

    // ── 当事人信息表（原告+代理人+被告+第三人全在一个大表里）──
    const partyRows = [headerRow('当事人信息', PAGE_W)];
    d.plaintiffs.forEach((p, i) => {
      partyRows.push(partyRow('原告'+(d.plaintiffs.length>1 ? i+1 : ''),
        p.type==='org' ? '（法人、非法人组织）' : '（自然人）', p));
    });
    if (d.agent) partyRows.push(agentRow(d.agent));
    d.defendants.forEach((p, i) => {
      partyRows.push(partyRow('被告'+(d.defendants.length>1 ? i+1 : ''),
        p.type==='org' ? '（法人、非法人组织）' : '（自然人）', p));
    });
    if (d.thirds && d.thirds.length) {
      d.thirds.forEach((p, i) => {
        partyRows.push(partyRow('第三人'+(d.thirds.length>1 ? i+1 : ''),
          p.type==='org' ? '（法人、非法人组织）' : '（自然人）', p));
      });
    }
    docChildren.push(new Table({ width:{size:PAGE_W,type:WidthType.DXA}, columnWidths:[LEFT_P,RIGHT_P], rows:partyRows }));
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing:{before:0,after:0} }));

    // ── 诉讼请求表 ──
    const caseTypeFacts = getFactsFields(state.caseType);
    const claimRows = [headerRow('诉讼请求', PAGE_W)];
    // First row = description text only (no user content)
    claimRows.push(dataRow('（可完整表述诉讼请求；为方便、准确梳理要点，相关内容请在下方要素式表格中填写）', ''));
    // Case-specific claim fields
    const claimFields = getClaimFields(state.caseType);
    claimFields.forEach(([key, label, hint]) => {
      const cl = label.replace(/^【.*?】/,'').trim();
      const cv = d.claims?.[key]||'';
      claimRows.push(dataRow(cl, cv || hint || ''));
    });
    claimRows.push(dataRow('是否主张诉讼费用', d.claims?.lawyerFee==='yes'?'是☑  否□':'是□  否☑'));
    claimRows.push(dataRow('其他请求', d.claims?.other||''));
    claimRows.push(dataRow('标的总额', d.claims?.total||''));
    docChildren.push(new Table({ width:{size:PAGE_W,type:WidthType.DXA}, columnWidths:[LEFT_D,RIGHT_D], rows:claimRows }));
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing:{before:0,after:0} }));

    // ── 管辖和诉前保全表 ──
    const jRows = [headerRow('约定管辖和诉前保全', PAGE_W)];
    jRows.push(dataRow('1. 有无仲裁、法院管辖约定', d.jurisdiction?.basis ? '有☑  无□\n合同条款及内容：'+d.jurisdiction.basis : '有□  无☑'));
    jRows.push(dataRow('2. 是否已经诉前保全', d.claims?.preservation==='yes'?'是☑\n保全法院：\n保全时间：\n保全案号：':'是□  否☑'));
    docChildren.push(new Table({ width:{size:PAGE_W,type:WidthType.DXA}, columnWidths:[LEFT_D,RIGHT_D], rows:jRows }));
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing:{before:0,after:0} }));

    // ── 事实与理由表 ──
    const factsRows = [headerRow('事实与理由', PAGE_W)];
    factsRows.push(dataRow('（可完整表述纠纷涉及的事实与理由；为方便、准确梳理要点，相关内容请在下方要素式表格中填写）', ''));
    caseTypeFacts.forEach(([key, label, hint]) => {
      const dl = label.replace(/^【.*?】/, '').trim();
      const fval = d.facts?.[key]||'';
      factsRows.push(dataRow(dl, fval || hint || ''));
    });
    docChildren.push(new Table({ width:{size:PAGE_W,type:WidthType.DXA}, columnWidths:[LEFT_D,RIGHT_D], rows:factsRows }));
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing:{before:0,after:0} }));

    // ── 调解意愿表（完整3行） ──
    const medRows = [headerRow('对纠纷解决方式的意愿', PAGE_W)];
    // Row 1
    medRows.push(dataRow('是否了解调解作为非诉讼纠纷解决方式，能及时、高效、低成本、不伤和气地解决纠纷', '了解☑　　不了解□'));
    // Row 2 - 5 items
    const medItems = [
      '1. 立案后选择先行调解的，可以很快启动调解程序。如不同意调解，法院将依程序开庭审理案件，但可能需要经过较长一段时间的排期等待，且审理、执行周期相对较长。\n了解☑　　不了解□',
      '2. 选择先行调解，调解成功且自动履行的免交诉讼费用，申请司法确认的不交纳诉讼费用，要求出具调解书的减半交纳诉讼费用。\n了解☑　　不了解□',
      '3. 首次调解不成功，但仍有继续调解意愿的，可以选择更换调解组织和调解员再进行调解。调解无法达成一致意见的，法院将依程序排期开庭。\n了解☑　　不了解□',
      '4. 依照法律规定，调解具有保密性要求，调解过程不公开，调解协议未经当事人同意不得公开。\n了解☑　　不了解□',
      '5. 调解达成的协议具有法律效力，可以依照法律规定申请司法确认，具有强制执行效力。\n了解☑　　不了解□',
    ];
    medRows.push(dataRow('是否了解先行调解解决纠纷的好处', medItems.join('\n')));
    // Row 3 - 是否考虑
    const medYes2 = d.jurisdiction?.mediation === 'yes';
    medRows.push(dataRow('是否考虑先行调解',
      (medYes2?'是☑':'是□') + '\n' + (!medYes2?'否☑':'否□') + '\n暂不确定，想要了解更多内容□'));
    docChildren.push(new Table({ width:{size:PAGE_W,type:WidthType.DXA}, columnWidths:[LEFT_D,RIGHT_D], rows:medRows }));

    // ── 签名 ──
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing:{before:300,after:100}, alignment:AlignmentType.RIGHT,
      children:[r('具状人（签字、盖章）：')] }));
    docChildren.push(new Paragraph({ alignment: AlignmentType.LEFT,  spacing:{before:0,after:100}, alignment:AlignmentType.RIGHT,
      children:[r('日期：'+(d.jurisdiction?.date||new Date().toLocaleDateString('zh-CN')))] }));

    const doc = new Document({ sections:[{
      properties:{ page:{ size:{width:12240,height:15840}, margin:{top:1440,right:1800,bottom:1440,left:1800} } },
      children: docChildren
    }]});

    const blob = await Packer.toBlob(doc);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (document.getElementById('export-filename').value||'要素式起诉状') + '.docx';
    a.click();
    URL.revokeObjectURL(url);
    showToast('DOCX 文件已生成并下载', 'success');
  } catch(e) {
    showToast('DOCX 生成失败：' + e.message, 'error');
    console.error('DOCX error:', e);
  }
}


function exportHtml() {
  syncFormData();
  const content = buildDocHtml();
  const full = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>要素式起诉状</title>
    <style>body{font-family:'Noto Serif SC','SimSun',serif;max-width:800px;margin:40px auto;padding:0 20px;font-size:14px;line-height:2;}
    .doc-title{text-align:center;font-size:20px;font-weight:700;margin-bottom:20px;}
    .doc-subtitle{text-align:center;color:#666;margin-bottom:30px;}
    .doc-section-title{font-size:15px;font-weight:700;border-bottom:2px solid #C9A84C;padding-bottom:4px;margin:20px 0 8px;}
    .doc-table{width:100%;border-collapse:collapse;margin-bottom:16px;font-size:13px;}
    .doc-table th{background:#D9E2F3;padding:8px 12px;text-align:center;border:1px solid #B0C4DE;}
    .doc-table td{border:1px solid #B0C4DE;padding:7px 12px;vertical-align:top;}
    .doc-table td:first-child{background:#F2F2F2;width:34%;}
    </style></head><body>${content}</body></html>`;
  const blob = new Blob([full], {type: 'text/html;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = (document.getElementById('export-filename').value || '要素式起诉状') + '.html';
  a.click();
  URL.revokeObjectURL(url);
  showToast('HTML 文件已下载', 'success');
}

// ============================================================
// History
// ============================================================
function addHistory(entry) {
  state.history.unshift(entry);
  if (state.history.length > 20) state.history = state.history.slice(0, 20);
  localStorage.setItem('bude_history', JSON.stringify(state.history));
  renderHistory();
}

function renderHistory() {
  const tbody = document.getElementById('history-tbody');
  if (!state.history.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--gray);padding:24px;font-size:13px;">暂无转换记录</td></tr>';
    return;
  }
  tbody.innerHTML = state.history.map((h, i) => `
    <tr>
      <td style="font-family:'JetBrains Mono',monospace;font-size:12px;text-align:left;">${h.name}</td>
      <td>${h.caseType}</td>
      <td style="font-size:12px;color:var(--gray);text-align:left;">${h.parties}</td>
      <td style="font-size:12px;color:var(--gray);text-align:left;">${h.time}</td>
      <td><span class="status-pill ${h.status === 'success' ? 'status-success' : 'status-error'}">${h.status === 'success' ? '✓ 成功' : '✗ 失败'}</span></td>
      <td>${h.status === 'success' ? `<button class="btn btn-outline btn-sm" onclick="reloadHistory(${i})">重新加载</button>` : ''}</td>
    </tr>
  `).join('');
}

function reloadHistory(i) {
  showToast('已重新加载历史记录，请重新上传文件', 'info');
}

// ============================================================
// Utils
// ============================================================
function esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function showToast(msg, type = '') {
  const ctn = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  ctn.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300); }, 3500);
}

// ============================================================
// Init
// ============================================================
function init() {
  // API key + model restored in initAiPanel()

  // Drag/drop events
  const zones = document.querySelectorAll('.upload-zone');
  zones.forEach(z => {
    z.addEventListener('dragover', e => { e.preventDefault(); z.classList.add('dragover'); });
    z.addEventListener('dragleave', () => z.classList.remove('dragover'));
  });

  // Default date
  const jDateEl = document.getElementById('j-date');
  if (jDateEl) jDateEl.value = new Date().toISOString().split('T')[0];

  // Init facts fields with default
  buildFactsSection();

  // Render history
  renderHistory();

  // Case type change
  document.getElementById('caseType').addEventListener('change', function() {
    state.caseType = this.value;
    state.caseTypeName = CASE_TYPE_NAMES[this.value] || '民事纠纷';
    buildFactsSection();
  });

  // AI Panel init
  initAiPanel();
}

// ============================================================
// AI 助手面板逻辑
// ============================================================
const AI_MODELS = [
  { group: '阿里云百炼', items: [
    { value: 'qwen-turbo', label: 'Qwen Turbo', desc: '速度最快，适合简单文书', badge: '快速' },
    { value: 'qwen-plus', label: 'Qwen Plus', desc: '速度与效果均衡，推荐首选', badge: '推荐' },
    { value: 'qwen-max', label: 'Qwen Max', desc: '效果最佳，适合复杂案件', badge: '精准' },
    { value: 'qwen-long', label: 'Qwen Long', desc: '超长文档专用（128K）', badge: '长文' },
    { value: 'qwen2.5-72b-instruct', label: 'Qwen2.5 72B', desc: '开源旗舰，推理能力强', badge: '' },
  ]},
  { group: 'DeepSeek', items: [
    { value: 'deepseek-chat', label: 'DeepSeek Chat', desc: '中文理解出色（需配置endpoint）', badge: '' },
    { value: 'deepseek-reasoner', label: 'DeepSeek Reasoner', desc: '推理链模式，精度高', badge: '' },
  ]},
  { group: 'OpenAI 兼容', items: [
    { value: 'gpt-4o', label: 'GPT-4o', desc: '需要OpenAI Key及代理', badge: '' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini', desc: '轻量快速，成本低', badge: '' },
  ]},
];


let aiPanelOpen = false;
let selectedModel = localStorage.getItem('bude_model') || 'qwen-plus';

const MODEL_ENDPOINT_MAP = {
  'qwen-turbo': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  'qwen-plus': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  'qwen-max': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  'qwen-long': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  'qwen2.5-72b-instruct': 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions',
  'deepseek-chat': 'https://api.deepseek.com/chat/completions',
  'deepseek-reasoner': 'https://api.deepseek.com/chat/completions',
  'gpt-4o': 'https://api.openai.com/v1/chat/completions',
  'gpt-4o-mini': 'https://api.openai.com/v1/chat/completions'
};

function getRecommendedEndpoint(model) {
  return MODEL_ENDPOINT_MAP[model] || 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions';
}

function getAiConfig() {
  return {
    model: selectedModel || document.getElementById('modelSelect').value || 'qwen-plus',
    apiKey: (document.getElementById('apiKey')?.value || '').trim(),
    baseUrl: (document.getElementById('apiBaseUrl')?.value || '').trim() || getRecommendedEndpoint(selectedModel),
    infer: !!document.getElementById('inferToggle')?.checked
  };
}

function saveAiConfig(showMessage) {
  const cfg = getAiConfig();
  localStorage.setItem('bude_model', cfg.model);
  localStorage.setItem('bude_apikey', cfg.apiKey);
  localStorage.setItem('bude_baseurl', cfg.baseUrl);
  localStorage.setItem('bude_infer', String(cfg.infer));
  const saveEl = document.getElementById('config-save-status');
  if (saveEl) {
    saveEl.innerHTML = '保存状态：<span style="color:#3da066;">已保存</span>';
  }
  updateKeyStatus(cfg.apiKey);
  updateEndpointHint();
  if (showMessage) showToast('AI 配置已保存到当前浏览器', 'success');
}

function restoreAiConfig() {
  const savedKey = localStorage.getItem('bude_apikey') || '';
  const savedBaseUrl = localStorage.getItem('bude_baseurl') || getRecommendedEndpoint(selectedModel);
  const savedInfer = localStorage.getItem('bude_infer');
  document.getElementById('apiKey').value = savedKey;
  document.getElementById('apiBaseUrl').value = savedBaseUrl;
  if (savedInfer === 'false') {
    document.getElementById('inferToggle').checked = false;
  } else {
    document.getElementById('inferToggle').checked = true;
  }
  updateKeyStatus(savedKey);
  updateInferToggle();
  updateEndpointHint();
}

function initAiPanel() {
  restoreAiConfig();

  document.getElementById('apiKey').addEventListener('input', e => {
    updateKeyStatus(e.target.value);
    markConfigDirty();
  });
  document.getElementById('apiBaseUrl').addEventListener('input', () => {
    updateEndpointHint(true);
    markConfigDirty();
  });
  document.getElementById('inferToggle').addEventListener('change', () => {
    updateInferToggle();
    markConfigDirty();
  });

  renderModelCards();
  updateAiBtnLabel();
  updateAiPanelStatus();
  updateEndpointHint();
}

function markConfigDirty() {
  const saveEl = document.getElementById('config-save-status');
  if (saveEl) {
    saveEl.innerHTML = '保存状态：<span style="color:#CAA769;">待保存</span>';
  }
}

function renderModelCards() {
  const container = document.getElementById('model-cards');
  let html = '';
  AI_MODELS.forEach(group => {
    html += `<div style="font-size:10px;color:#3a3a3a;letter-spacing:0.06em;margin:10px 0 5px;text-transform:uppercase;">${group.group}</div>`;
    group.items.forEach(m => {
      const active = m.value === selectedModel;
      html += `<div onclick="selectModel('${m.value}')" style="padding:9px 12px;border-radius:6px;cursor:pointer;border:1px solid ${active?'rgba(202,167,105,0.45)':'#222'};background:${active?'rgba(202,167,105,0.07)':'#111'};transition:all 0.15s;display:flex;align-items:center;gap:10px;" onmouseover="if('${m.value}'!==selectedModel)this.style.borderColor='#333'" onmouseout="if('${m.value}'!==selectedModel)this.style.borderColor='#222'">
        <div style="width:7px;height:7px;border-radius:50%;background:${active?'#CAA769':'#2a2a2a'};flex-shrink:0;transition:background 0.15s;"></div>
        <div style="flex:1;min-width:0;">
          <div style="font-size:12px;color:${active?'#CAA769':'#888'};font-weight:${active?'600':'400'};font-family:'JetBrains Mono',monospace;">${m.label}${m.badge?` <span style="font-size:9px;padding:1px 6px;border-radius:3px;background:rgba(202,167,105,0.15);color:#967830;">${m.badge}</span>`:''}</div>
          <div style="font-size:10px;color:#3a3a3a;margin-top:1px;">${m.desc}</div>
        </div>
      </div>`;
    });
  });
  container.innerHTML = html;
}

function selectModel(val) {
  const prevModel = selectedModel;
  selectedModel = val;
  document.getElementById('modelSelect').value = val;
  const endpointInput = document.getElementById('apiBaseUrl');
  const current = (endpointInput.value || '').trim();
  const previousRecommended = getRecommendedEndpoint(prevModel);
  if (!current || current === previousRecommended) {
    endpointInput.value = getRecommendedEndpoint(val);
  }
  renderModelCards();
  updateAiBtnLabel();
  updateAiPanelStatus();
  updateEndpointHint();
  markConfigDirty();
}

function updateAiBtnLabel() {
  const el = document.getElementById('ai-btn-model');
  if (!el) return;
  const found = AI_MODELS.flatMap(g=>g.items).find(m=>m.value===selectedModel);
  el.textContent = found ? found.label : selectedModel;
}

function updateAiPanelStatus() {
  const found = AI_MODELS.flatMap(g=>g.items).find(m=>m.value===selectedModel);
  const el = document.getElementById('ai-panel-status');
  if (el && found) el.textContent = found.label + (found.badge?' · '+found.badge:'');
}

function updateKeyStatus(val) {
  const el = document.getElementById('key-status');
  if (!el) return;
  if (!val || val.trim().length < 10) {
    el.textContent = '未配置'; el.style.color = '#555';
  } else {
    el.textContent = '已配置 (' + val.trim().slice(0,6) + '...)'; el.style.color = '#3da066';
  }
}

function updateEndpointHint(isManualEdit) {
  const hintEl = document.getElementById('endpoint-hint');
  const statusEl = document.getElementById('endpoint-status');
  const current = (document.getElementById('apiBaseUrl')?.value || '').trim();
  const recommended = getRecommendedEndpoint(selectedModel);
  if (hintEl) {
    hintEl.textContent = current === recommended
      ? '当前使用推荐接口地址'
      : (isManualEdit ? '当前为自定义接口地址' : '可自定义兼容接口地址');
  }
  if (statusEl) {
    statusEl.textContent = '未校验';
    statusEl.style.color = '#555';
  }
}

function updateInferToggle() {
  const checked = document.getElementById('inferToggle').checked;
  document.getElementById('inferTrack').style.background = checked ? '#CAA769' : '#333';
  document.getElementById('inferThumb').style.left = checked ? '16px' : '2px';
}

function toggleApiKeyVisibility() {
  const input = document.getElementById('apiKey');
  const btn = document.getElementById('toggleApiKeyBtn');
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '隐藏';
  } else {
    input.type = 'password';
    btn.textContent = '显示';
  }
}

async function testAiConnection() {
  const btn = document.getElementById('test-config-btn');
  const statusEl = document.getElementById('endpoint-status');
  const cfg = getAiConfig();
  if (!cfg.apiKey) {
    showToast('请先填写 API 密钥', 'error');
    return;
  }
  if (!cfg.baseUrl) {
    showToast('请先填写接口地址', 'error');
    return;
  }
  btn.disabled = true;
  btn.textContent = '测试中...';
  if (statusEl) {
    statusEl.textContent = '校验中';
    statusEl.style.color = '#CAA769';
  }
  try {
    const resp = await fetch(cfg.baseUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + cfg.apiKey
      },
      body: JSON.stringify({
        model: cfg.model,
        messages: [{ role: 'user', content: '请仅回复“ok”。' }],
        temperature: 0,
        max_tokens: 10
      })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      throw new Error(err.error?.message || err.message || ('HTTP ' + resp.status));
    }
    const data = await resp.json();
    const content = data.choices?.[0]?.message?.content || '';
    if (!content) throw new Error('接口已响应，但未返回有效内容');
    if (statusEl) {
      statusEl.textContent = '连接成功';
      statusEl.style.color = '#3da066';
    }
    showToast('连接测试成功：模型与接口可正常调用', 'success');
    saveAiConfig(false);
  } catch (e) {
    if (statusEl) {
      statusEl.textContent = '连接失败';
      statusEl.style.color = '#c0392b';
    }
    showToast('连接测试失败：' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '连接测试';
  }
}

function toggleAiPanel() {
  const panel = document.getElementById('ai-panel');
  const overlay = document.getElementById('ai-panel-overlay');
  if (!aiPanelOpen) {
    panel.style.display = 'flex';
    overlay.style.display = 'block';
    requestAnimationFrame(() => { panel.style.transform = 'translateX(0)'; });
    aiPanelOpen = true;
    updateAiPanelStatus();
    updateKeyStatus(document.getElementById('apiKey').value);
    updateEndpointHint();
  } else {
    closeAiPanel();
  }
}

function closeAiPanel() {
  const panel = document.getElementById('ai-panel');
  const overlay = document.getElementById('ai-panel-overlay');
  panel.style.transform = 'translateX(100%)';
  overlay.style.display = 'none';
  setTimeout(() => { if (!aiPanelOpen) panel.style.display = 'none'; }, 300);
  aiPanelOpen = false;
}


init();
updateTemplateMetaCard();