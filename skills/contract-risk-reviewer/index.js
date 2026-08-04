/**
 * 法律合同风险审查系统 v1.0
 * 
 * 专业级合同风险审查引擎
 * - 20+ 类风险条款识别
 * - 法律依据引用
 * - 修改建议生成
 * - 风险评分算法
 * 
 * 定价：¥99/月 | $39.99/月
 * 企业主体：上海冰月网络科技有限公司
 */

class ContractRiskReviewer {

  // ============================================================
  // 风险条款规则库（20+ 类别）
  // ============================================================
  static riskRules = [
    // --- 1. 违约责任 ---
    {
      id: 'breach-vague',
      category: '违约责任',
      severity: 'HIGH',
      keywords: ['违约责任', '违约', '不履行合同', '未按照'],
      patterns: [
        /违约.{0,30}承担.{0,20}责任/,
        /如一方违约.{0,50}/,
      ],
      check: (text) => {
        // 检查违约责任是否明确具体
        const hasSpecificPenalty = /违约金.*\d|赔偿.*\d.*元|按.*%.*计算|每日.*万分之|滞纳金/.test(text);
        const hasBreachClause = /违约责任|违约方|不履行合同/.test(text);
        
        if (hasBreachClause && !hasSpecificPenalty) {
          return {
            found: true,
            issue: '违约责任条款存在，但未明确具体赔偿金额或计算方式',
            suggestion: '建议明确约定：1) 违约金具体金额或计算公式；2) 赔偿范围（直接损失/间接损失）；3) 是否包含律师费、诉讼费等维权成本。',
            revised: `任何一方违约，应向守约方支付违约金人民币【】元。违约金不足以弥补损失的，违约方还应赔偿差额部分。赔偿范围包括但不限于直接损失、合理的律师费、诉讼费、保全费、鉴定费等维权费用。`,
            legalBasis: '《民法典》第 584 条：损失赔偿额应当相当于因违约所造成的损失，包括合同履行后可以获得的利益。'
          };
        }
        return { found: false };
      }
    },

    // --- 2. 管辖权陷阱 ---
    {
      id: 'jurisdiction-risk',
      category: '管辖权',
      severity: 'HIGH',
      keywords: ['管辖', '法院', '仲裁', '争议解决'],
      check: (text, myRole) => {
        // 检查管辖约定是否对自己不利
        const jurisdictionMatch = text.match(/(?:由|向|提交).*?(?:甲方|乙方|.*?)所在地.*?(?:人民法院|仲裁委员会)/g);
        
        if (jurisdictionMatch) {
          const clauses = jurisdictionMatch;
          for (const clause of clauses) {
            // 如果约定在对方所在地
            if ((myRole === '甲方' && clause.includes('乙方')) || 
                (myRole === '乙方' && clause.includes('甲方'))) {
              return {
                found: true,
                issue: `争议管辖约定在对方所在地，增加维权成本`,
                detail: `当前条款：${clause}`,
                suggestion: '建议修改为：1) 原告所在地法院；2) 合同签订地法院；3) 双方认可的第三方城市（如北京、上海）。异地诉讼将大幅增加时间和金钱成本。',
                revised: '因本合同引起的争议，双方应友好协商解决；协商不成的，任何一方均可向原告所在地人民法院提起诉讼。',
                legalBasis: '《民事诉讼法》第 35 条：合同双方当事人可以在书面合同中协议选择被告住所地、合同履行地、合同签订地、原告住所地、标的物所在地人民法院管辖。'
              };
            }
          }
          // 检查是否同时约定了法院和仲裁（冲突）
          const hasCourt = /人民法院|法院/.test(text);
          const hasArbitration = /仲裁委员会|仲裁/.test(text);
          if (hasCourt && hasArbitration) {
            return {
              found: true,
              issue: '同时约定了法院管辖和仲裁，条款冲突可能导致无效',
              suggestion: '只能选择一种方式：要么约定法院管辖，要么约定仲裁。建议删除其中一个。',
              revised: '因本合同引起的争议，双方应友好协商解决；协商不成的，任何一方均可向【】仲裁委员会按照该会现行仲裁规则进行仲裁。（或者：向【】人民法院提起诉讼。）',
              legalBasis: '《仲裁法》第 16 条：仲裁协议应当明确选定仲裁委员会。同时约定诉讼和仲裁的，仲裁协议无效。'
            };
          }
        }
        return { found: false };
      }
    },

    // --- 3. 单方权利不对等 ---
    {
      id: 'unilateral-rights',
      category: '权利义务对等',
      severity: 'HIGH',
      keywords: ['甲方有权', '乙方有权', '甲方可以', '乙方可以', '单方'],
      check: (text, myRole) => {
        // 统计甲方/乙方的权利条款数量
        const partyARights = (text.match(/甲方有权/g) || []).length + (text.match(/甲方可以/g) || []).length;
        const partyBRights = (text.match(/乙方有权/g) || []).length + (text.match(/乙方可以/g) || []).length;
        
        const imbalance = Math.abs(partyARights - partyBRights);
        if (imbalance >= 2) {
          const favoredParty = partyARights > partyBRights ? '甲方' : '乙方';
          const mySide = favoredParty === (myRole === '甲方' ? '甲方' : '乙方');
          
          return {
            found: true,
            issue: `合同权利义务明显不对等，${favoredParty}拥有${Math.max(partyARights, partyBRights)} 项权利，另一方仅${Math.min(partyARights, partyBRights)} 项`,
            suggestion: mySide 
              ? '虽然当前对你有利，但过度不对等的条款可能被认定为格式条款而无效。建议适当平衡以增加合同稳定性。'
              : '建议增加对等权利：1) 对等的解除权；2) 对等的知情权；3) 对等的抗辩权。',
            revised: '双方均享有以下对等权利：1) 知情权（了解合同履行情况）；2) 抗辩权（在对方未履行时有权拒绝履行）；3) 解除权（符合法定条件时单方解除）。',
            legalBasis: '《民法典》第 497 条：提供格式条款一方不合理地免除或者减轻其责任、加重对方责任、限制对方主要权利的，该格式条款无效。'
          };
        }
        return { found: false };
      }
    },

    // --- 4. 保密条款缺失 ---
    {
      id: 'confidentiality-missing',
      category: '保密条款',
      severity: 'MEDIUM',
      check: (text) => {
        const hasConfidentiality = /保密|商业秘密|机密|不得泄露|不得披露/.test(text);
        const hasContractDetails = /合同标的|服务内容|合作模式|技术方案|价格/.test(text);
        
        if (!hasConfidentiality && hasContractDetails) {
          return {
            found: true,
            issue: '合同涉及商业信息但未约定保密条款',
            suggestion: '建议增加保密条款，明确：1) 保密信息范围；2) 保密期限；3) 违约责任；4) 例外情形。',
            revised: `双方应对本合同内容及履行过程中获知的对方商业秘密承担保密义务。保密期限为本合同有效期内及合同终止后【三】年。任何一方违反保密义务，应向对方支付违约金人民币【】元，并赔偿因此造成的全部损失。下列信息不属于保密信息：a) 已公开的信息；b) 依法应披露的信息；c) 独立开发获得的信息。`,
            legalBasis: '《民法典》第 501 条：当事人在订立合同过程中知悉的商业秘密或者其他应当保密的信息，无论合同是否成立，不得泄露或者不正当地使用。'
          };
        }
        return { found: false };
      }
    },

    // --- 5. 知识产权归属不明 ---
    {
      id: 'ip-unclear',
      category: '知识产权',
      severity: 'HIGH',
      keywords: ['知识产权', '著作权', '版权', '专利', '成果', '交付物', '所有权'],
      check: (text) => {
        const hasWorkProduct = /交付物|成果|作品|开发|设计|创作|报告/.test(text);
        const hasIPClause = /知识产权.*归|著作权.*归|所有权.*归|版权.*归/.test(text);
        
        if (hasWorkProduct && !hasIPClause) {
          return {
            found: true,
            issue: '合同涉及成果交付，但未明确知识产权归属',
            suggestion: '必须明确约定：1) 交付成果的知识产权归谁所有；2) 是否允许对方继续使用；3) 署名权如何处理。',
            revised: `本合同项下产生的所有交付成果（包括但不限于报告、代码、设计、文案等）的知识产权（含著作权、专利权等）归【甲方/乙方】所有。另一方在合同有效期内享有非独占的、不可转让的使用权。未经权利人书面同意，不得将成果转让给第三方或用于本合同以外的用途。`,
            legalBasis: '《著作权法》第 19 条：受委托创作的作品，著作权的归属由委托人和受托人通过合同约定。未作明确约定的，著作权属于受托人。'
          };
        }
        return { found: false };
      }
    },

    // --- 6. 付款条件模糊 ---
    {
      id: 'payment-vague',
      category: '付款条款',
      severity: 'HIGH',
      keywords: ['付款', '支付', '费用', '金额', '元', '结算'],
      check: (text) => {
        const hasPayment = /付款|支付|费用|价款/.test(text);
        const hasSpecificAmount = /\d+\s*[万元亿]|￥|RMB|人民币.*\d/.test(text);
        const hasPaymentTerms = /(\d+).*个工作日内.*支付|签订.*后.*支付|交付.*后.*支付|验收.*后.*支付/.test(text);
        const hasTaxClause = /税|发票|含税|不含税/.test(text);
        
        if (hasPayment && (!hasSpecificAmount || !hasPaymentTerms)) {
          return {
            found: true,
            issue: '付款条款存在但不完整（缺少金额/时间/条件中的至少一项）',
            suggestion: '付款条款必须包含：1) 具体金额或计算公式；2) 付款时间节点；3) 付款触发条件；4) 是否含税；5) 发票要求。',
            revised: `甲方应于本合同签订后【】个工作日内，向乙方支付合同总价款人民币【】元（含税/不含税）。乙方应在收到款项后【】个工作日内开具等额合规增值税【专用/普通】发票。`,
            legalBasis: '《民法典》第 510 条：合同生效后，当事人就价款等内容没有约定或约定不明确的，可以协议补充。'
          };
        }
        return { found: false };
      }
    },

    // --- 7. 合同解除权不对等 ---
    {
      id: 'termination-imbalance',
      category: '解除权',
      severity: 'HIGH',
      keywords: ['解除', '终止', '单方解除'],
      check: (text) => {
        const partyACanTerminate = (text.match(/甲方.*(?:有权|可以).*解除/g) || []).length;
        const partyBCanTerminate = (text.match(/乙方.*(?:有权|可以).*解除/g) || []).length;
        const onlyOneSide = partyACanTerminate > 0 && partyBCanTerminate === 0 ||
                           partyBCanTerminate > 0 && partyACanTerminate === 0;
        
        if (onlyOneSide) {
          return {
            found: true,
            issue: '仅单方享有合同解除权，另一方无权解除',
            suggestion: '建议约定双方对等的解除权，或至少约定另一方在特定条件下（如对方严重违约）的解除权。',
            revised: '任何一方在以下情形下有权书面通知对方解除本合同：a) 对方严重违约且经催告后【15】日内未纠正；b) 对方破产、解散或被吊销营业执照；c) 因不可抗力导致合同目的无法实现。',
            legalBasis: '《民法典》第 563 条：当事人一方迟延履行主要债务，经催告后在合理期限内仍未履行的，对方可以解除合同。'
          };
        }
        return { found: false };
      }
    },

    // --- 8. 免责条款过宽 ---
    {
      id: 'excessive-exemption',
      category: '免责条款',
      severity: 'HIGH',
      keywords: ['免责', '不承担', '免于', '不负责'],
      check: (text) => {
        // 检查是否有过度免责
        const broadExemptions = /(?:任何.*损失|一切.*责任|概不负责|不承担任何.*责任|免除.*全部)/.test(text);
        const noLimitOnExemption = !/但书|但不包括|除外|故意|重大过失/.test(text);
        
        if (broadExemptions && noLimitOnExemption) {
          return {
            found: true,
            issue: '免责条款过于宽泛，可能免除故意和重大过失责任',
            suggestion: '免责条款不能免除故意或重大过失造成的损害，否则无效。建议增加例外情形。',
            revised: '除以下情形外，任何一方不对间接损失（包括利润损失、商业机会丧失等）承担责任：a) 因故意或重大过失造成的损害；b) 违反保密义务；c) 侵犯知识产权；d) 违反法律法规。',
            legalBasis: '《民法典》第 506 条：合同中的下列免责条款无效：（一）造成对方人身损害的；（二）因故意或者重大过失造成对方财产损失的。'
          };
        }
        return { found: false };
      }
    },

    // --- 9. 期限/时效缺失 ---
    {
      id: 'duration-missing',
      category: '合同期限',
      severity: 'MEDIUM',
      check: (text) => {
        const hasTerm = /有效期|期限|自.*至|从.*到|\d+\s*年|\d+\s*月|\d+\s*日/.test(text);
        const hasServiceContent = /服务|合作|提供|履行/.test(text);
        
        if (!hasTerm && hasServiceContent) {
          return {
            found: true,
            issue: '合同涉及服务/合作履行，但未明确有效期限',
            suggestion: '建议明确合同起止日期，以及是否自动续约。',
            revised: '本合同有效期自【年】【月】【日】至【年】【月】【日】。合同期满前 30 日内，如双方均未书面提出终止，则本合同自动续期【一】年，续期次数不限。',
            legalBasis: '《民法典》第 160 条：民事法律行为可以附期限。'
          };
        }
        return { found: false };
      }
    },

    // --- 10. 自动续约陷阱 ---
    {
      id: 'auto-renewal-risk',
      category: '续约条款',
      severity: 'MEDIUM',
      keywords: ['自动续约', '自动续期', '顺延'],
      check: (text) => {
        const hasAutoRenewal = /自动续(?:约|期)|自动顺延|期满.*自动/.test(text);
        const hasNoticePeriod = /提前.*(?:通知|书面通知|通知期)|.*个工作.*通知/.test(text);
        const hasPriceChange = /续约.*价格|续约.*费用|续约.*金额/.test(text);
        
        if (hasAutoRenewal && (!hasNoticePeriod || !hasPriceChange)) {
          return {
            found: true,
            issue: '自动续约条款但未约定提前通知期和续约价格调整机制',
            suggestion: '建议约定：1) 提前多少天通知可以不续约；2) 续约时价格调整规则；3) 续约条件变更的通知义务。',
            revised: '本合同期满前【30】日内，如任何一方未书面通知对方不再续约，则本合同自动续期【一】年。续约价格调整幅度不得超过原价格的【10%】。任何一方调整续约条件的，应提前【60】日书面通知对方。',
            legalBasis: '《民法典》第 496 条：提供格式条款的一方应当遵循公平原则确定当事人之间的权利和义务。'
          };
        }
        return { found: false };
      }
    },

    // --- 11. 不可抗力条款 ---
    {
      id: 'force-majeure',
      category: '不可抗力',
      severity: 'LOW',
      check: (text) => {
        const hasForceMajeure = /不可抗力/.test(text);
        const hasContract = /合同|协议/.test(text);
        
        if (!hasForceMajeure && hasContract && text.length > 500) {
          return {
            found: true,
            issue: '合同未约定不可抗力条款',
            suggestion: '建议增加不可抗力条款，明确范围、通知义务和后果处理。',
            revised: '因不可抗力（包括但不限于地震、台风、洪水、火灾、战争、政府行为、重大疫情等）导致无法履行合同的，受影响方应在不可抗力发生后【7】日内书面通知对方，并提供相关证明。双方可协商延期履行、部分履行或解除合同，互不承担违约责任。',
            legalBasis: '《民法典》第 180 条：因不可抗力不能履行民事义务的，不承担民事责任。不可抗力是不能预见、不能避免且不能克服的客观情况。'
          };
        }
        return { found: false };
      }
    },

    // --- 12. 通知送达条款 ---
    {
      id: 'notice-delivery',
      category: '通知送达',
      severity: 'MEDIUM',
      keywords: ['通知', '送达', '联系方式', '地址'],
      check: (text) => {
        const hasNotice = /通知|送达/.test(text);
        const hasContactInfo = /地址|邮箱|电话|联系人/.test(text);
        const hasDeemedDelivery = /视为送达|视为已通知|送达时间/.test(text);
        
        if (!hasNotice || !hasDeemedDelivery) {
          return {
            found: true,
            issue: '缺少通知送达条款或未约定"视为送达"规则',
            suggestion: '建议约定具体的通知方式、送达地址和视为送达的规则。',
            revised: `双方确认以下联系方式为有效送达地址：甲方：地址【】，邮箱【】，联系人【】；乙方：地址【】，邮箱【】，联系人【】。通过快递寄送的，签收日视为送达日；通过电子邮件发送的，邮件进入对方系统之日视为送达日。任何一方变更联系方式，应提前【3】日书面通知对方。`,
            legalBasis: '《民法典》第 137 条：以非对话方式作出的意思表示，到达相对人时生效。'
          };
        }
        return { found: false };
      }
    },

    // --- 13. 连带责任风险 ---
    {
      id: 'joint-liability',
      category: '连带责任',
      severity: 'HIGH',
      keywords: ['连带责任', '连带保证', '共同承担', '连带赔偿'],
      check: (text, myRole) => {
        const hasJointLiability = /连带责任|连带保证|共同承担.*责任/.test(text);
        
        if (hasJointLiability) {
          return {
            found: true,
            issue: '合同约定了连带责任，可能使你承担超出预期范围的责任',
            suggestion: '连带责任意味着你可能需要为他人的行为承担全部责任。建议：1) 明确责任上限；2) 约定追偿权；3) 如可能，改为按份责任。',
            revised: '各方按照各自过错比例承担相应责任（按份责任），而非连带责任。任何一方承担责任后，有权就超出其应承担比例的部分向其他方追偿。',
            legalBasis: '《民法典》第 178 条：连带责任由法律规定或当事人约定。连带责任人不明确约定的，按照各自责任大小承担责任。'
          };
        }
        return { found: false };
      }
    },

    // --- 14. 定金/押金风险 ---
    {
      id: 'deposit-risk',
      category: '定金条款',
      severity: 'MEDIUM',
      keywords: ['定金', '押金', '保证金', '订金'],
      check: (text) => {
        const hasDeposit = /定金|押金|保证金/.test(text);
        const hasRefundRule = /退还|退回|返还|不予退还|没收/.test(text);
        const hasDepositPenalty = /定金.*双倍|双倍.*定金|定金罚/.test(text);
        
        if (hasDeposit && !hasRefundRule) {
          return {
            found: true,
            issue: '约定了定金/押金但未明确退还条件',
            suggestion: '必须明确：1) 什么条件下退还；2) 什么条件下没收；3) 退还时限。',
            revised: '本合同项下定金/保证金为人民币【】元。合同履行完毕后【3】个工作日内全额退还（无息）。如支付方违约，定金不予退还；如接收方违约，应双倍返还定金。',
            legalBasis: '《民法典》第 586-588 条：定金合同自实际交付定金时成立。债务人履行债务的，定金应当抵作价款或者收回。给付定金的一方不履行债务的，无权请求返还；收受定金的一方不履行债务的，应当双倍返还。'
          };
        }
        return { found: false };
      }
    },

    // --- 15. 竞业限制 ---
    {
      id: 'non-compete',
      category: '竞业限制',
      severity: 'HIGH',
      keywords: ['竞业', '竞争', '同业', '不得从事', '不得经营'],
      check: (text) => {
        const hasNonCompete = /竞业|竞争业务|同业|不得从事.*业务|不得经营/.test(text);
        const hasDuration = /(?:竞业|限制).*?(?:期限|时间|月|年)/.test(text);
        const hasCompensation = /补偿|补偿金|对价/.test(text);
        const hasScope = /地域|范围|行业/.test(text);
        
        if (hasNonCompete && (!hasDuration || !hasCompensation)) {
          return {
            found: true,
            issue: '竞业限制条款缺少期限或补偿约定，可能无效或显失公平',
            suggestion: '竞业限制必须约定：1) 具体期限（最长不超过 2 年）；2) 经济补偿金额；3) 限制范围。',
            revised: '竞业限制期限为合同终止后【12】个月。限制期间内，按月支付补偿金人民币【】元/月（不低于离职前 12 个月平均工资的 30%）。限制范围为【具体地域和行业】。',
            legalBasis: '《劳动合同法》第 23-24 条：竞业限制期限不得超过二年。用人单位应给予经济补偿。'
          };
        }
        return { found: false };
      }
    },

    // --- 16. 违约金过高 ---
    {
      id: 'excessive-penalty',
      category: '违约金',
      severity: 'MEDIUM',
      keywords: ['违约金', '罚金', '罚款', '赔偿'],
      check: (text) => {
        // 检查违约金是否超过合同金额的 30%
        const penaltyMatch = text.match(/违约金.*?(\d+(?:\.\d+)?)\s*[万元亿]/g);
        const totalMatch = text.match(/合同.*?(?:总|价)款.*?(\d+(?:\.\d+)?)\s*[万元亿]/g);
        
        if (penaltyMatch && totalMatch) {
          const penalty = parseFloat(penaltyMatch[0].match(/(\d+)/)[1]);
          const total = parseFloat(totalMatch[0].match(/(\d+)/)[1]);
          const ratio = penalty / total;
          
          if (ratio > 0.3) {
            return {
              found: true,
              issue: `违约金(${penalty}万)超过合同总额(${total}万)的 30%，可能被法院调减`,
              suggestion: '违约金一般不超过实际损失的 30%。过高部分法院有权调减。建议约定合理比例。',
              revised: `违约金为合同总价款的【10%-20%】，即人民币【】元。如实际损失超过违约金，守约方有权就超出部分要求赔偿。`,
              legalBasis: '《民法典》第 585 条：约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少。'
            };
          }
        }
        return { found: false };
      }
    },

    // --- 17. 个人信息保护 ---
    {
      id: 'personal-data',
      category: '数据保护',
      severity: 'HIGH',
      keywords: ['个人信息', '用户数据', '隐私', '收集', '处理'],
      check: (text) => {
        const hasPersonalData = /个人信息|用户数据|隐私|收集.*信息|处理.*数据/.test(text);
        const hasComplianceClause = /个人信息保护法|数据安全法|合规|同意|授权/.test(text);
        
        if (hasPersonalData && !hasComplianceClause) {
          return {
            found: true,
            issue: '合同涉及个人信息处理，但未约定数据合规义务',
            suggestion: '必须约定：1) 个人信息处理目的和范围；2) 获得用户同意的责任方；3) 数据安全义务；4) 泄露通知义务。',
            revised: '任何一方处理个人信息应遵守《个人信息保护法》相关规定，确保：a) 已获得信息主体的明确同意；b) 仅在授权范围内使用；c) 采取合理的安全保护措施；d) 发生数据泄露时 24 小时内通知对方。',
            legalBasis: '《个人信息保护法》第 13、21 条：处理个人信息应取得个人同意。委托处理个人信息的，应约定处理目的、期限、方式等。'
          };
        }
        return { found: false };
      }
    },

    // --- 18. 合同变更规则 ---
    {
      id: 'modification-rule',
      category: '合同变更',
      severity: 'LOW',
      keywords: ['变更', '修改', '补充'],
      check: (text) => {
        const hasModification = /变更|修改|补充/.test(text);
        const hasWrittenReq = /书面|双方.*同意.*方可/.test(text);
        
        if (!hasModification || !hasWrittenReq) {
          return {
            found: true,
            issue: '未约定合同变更需书面同意的规则',
            suggestion: '建议约定任何变更需双方书面同意，避免口头变更的争议。',
            revised: '本合同的任何变更、修改或补充须经双方协商一致并以书面形式作出，经双方签字盖章后生效。任何口头变更无效。',
            legalBasis: '《民法典》第 543 条：当事人协商一致，可以变更合同。'
          };
        }
        return { found: false };
      }
    },

    // --- 19. 转让限制 ---
    {
      id: 'assignment-restriction',
      category: '合同转让',
      severity: 'MEDIUM',
      keywords: ['转让', '权利义务转让', '分包', '转包'],
      check: (text) => {
        const hasAssignment = /转让|分包|转包|权利义务.*转让/.test(text);
        const hasRestriction = /未经.*同意|不得.*转让|书面.*同意/.test(text);
        
        if (hasAssignment && !hasRestriction) {
          return {
            found: true,
            issue: '合同涉及权利义务转让，但未限制单方转让',
            suggestion: '建议约定未经对方书面同意，不得转让合同权利义务。',
            revised: '未经对方事先书面同意，任何一方不得将本合同项下的权利义务全部或部分转让给第三方。违反本条约定的转让行为无效。',
            legalBasis: '《民法典》第 545 条：债权人可以将债权的全部或者部分转让给第三人，但按照合同性质不得转让的除外。'
          };
        }
        return { found: false };
      }
    },

    // --- 20. 争议解决成本 ---
    {
      id: 'dispute-cost',
      category: '争议解决成本',
      severity: 'MEDIUM',
      keywords: ['律师费', '诉讼费', '仲裁费', '维权费用'],
      check: (text) => {
        const hasDispute = /争议|纠纷|诉讼|仲裁/.test(text);
        const hasCostAllocation = /律师费.*承担|诉讼费.*承担|维权费用|合理费用/.test(text);
        
        if (hasDispute && !hasCostAllocation) {
          return {
            found: true,
            issue: '未约定维权费用（律师费、诉讼费等）由败诉方承担',
            suggestion: '建议约定败诉方承担胜诉方的合理维权费用，降低维权成本。',
            revised: '因本合同引起的争议，败诉方应承担胜诉方因此支出的合理费用，包括但不限于律师费、诉讼费、保全费、鉴定费、差旅费等。',
            legalBasis: '《民事诉讼法》及相关司法解释支持合理维权费用的主张。'
          };
        }
        return { found: false };
      }
    },
  ];

  // ============================================================
  // 风险等级定义
  // ============================================================
  static severityLevels = {
    HIGH: { score: 10, label: '高风险', color: '🔴', advice: '必须修改' },
    MEDIUM: { score: 5, label: '中风险', color: '🟡', advice: '建议修改' },
    LOW: { score: 2, label: '低风险', color: '🟢', advice: '可选优化' },
  };

  // ============================================================
  // 主审查函数
  // ============================================================
  static review(params) {
    const {
      contract_text: text = '',
      contract_type = '通用',
      my_role: myRole = '通用',
      depth = '标准'
    } = params;

    if (!text || text.length < 50) {
      return {
        error: true,
        message: '合同文本过短，请输入完整的合同内容（至少 50 字）'
      };
    }

    const risks = [];
    let totalScore = 0;

    // 执行所有规则检查
    for (const rule of this.riskRules) {
      try {
        const result = rule.check(text, myRole);
        if (result.found) {
          const level = this.severityLevels[rule.severity];
          risks.push({
            id: rule.id,
            category: rule.category,
            severity: rule.severity,
            severityLabel: level.label,
            severityIcon: level.color,
            advice: level.advice,
            issue: result.issue,
            detail: result.detail || '',
            suggestion: result.suggestion,
            revised: result.revised || '',
            legalBasis: result.legalBasis || '',
          });
          totalScore += level.score;
        }
      } catch (e) {
        // 规则执行失败不影响其他规则
        console.warn(`规则 ${rule.id} 执行失败:`, e.message);
      }
    }

    // 按严重程度排序
    risks.sort((a, b) => {
      const order = { HIGH: 0, MEDIUM: 1, LOW: 2 };
      return order[a.severity] - order[b.severity];
    });

    // 计算风险评分（0-100）
    const maxPossible = this.riskRules.length * 10;
    const riskScore = Math.min(100, Math.round((totalScore / maxPossible) * 100));

    // 生成整体建议
    const highRisks = risks.filter(r => r.severity === 'HIGH');
    const mediumRisks = risks.filter(r => r.severity === 'MEDIUM');
    const lowRisks = risks.filter(r => r.severity === 'LOW');

    let summary = `合同风险审查完成。共识别 ${risks.length} 项风险：`;
    summary += `\n🔴 高风险 ${highRisks.length} 项（必须修改）`;
    summary += `\n🟡 中风险 ${mediumRisks.length} 项（建议修改）`;
    summary += `\n🟢 低风险 ${lowRisks.length} 项（可选优化）`;
    summary += `\n综合风险评分：${riskScore}/100`;
    
    if (riskScore > 60) {
      summary += '\n\n⚠️ 风险评分较高，建议全面修改后再签署。';
    } else if (riskScore > 30) {
      summary += '\n\n📋 存在部分中高风险，建议优先处理高风险条款。';
    } else {
      summary += '\n\n✅ 整体风险可控，建议优化低风险条款。';
    }

    return {
      riskScore,
      totalRisks: risks.length,
      highRisks: highRisks.length,
      mediumRisks: mediumRisks.length,
      lowRisks: lowRisks.length,
      risks,
      summary,
      contract_type: contract_type,
      my_role: myRole,
      reviewDepth: depth,
      reviewedAt: new Date().toISOString(),
      disclaimer: '本工具仅提供风险提示参考，不构成正式法律意见。重大合同请咨询专业律师。',
    };
  }
}

module.exports = ContractRiskReviewer;
