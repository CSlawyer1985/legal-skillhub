# 地名对应

城市、国家和区域有时会因政治、后殖民或后苏联原因而更名。同一实体地点在不同时期或不同来源中可能以不同名称出现。在筛查警报两侧比较出生地、地址或司法辖区时，朴素的字符串比较会在这些情况下失败。

本参考文件编目与制裁和筛查语境相关的有据可查的对应关系。在以下环节使用：
- **第 0 层解析**——提取出生地和地址字段时，对照本清单进行规范化
- **第 2 层 TP-2 触发**——出生地市级匹配接受有据可查的对应关系为同一城市
- **第 3 层研究**——搜索背景信息时，尝试某地的两个名称以扩大覆盖面

对有据可查的对应关系的匹配，就 TP-2 目的而言视为市级匹配——政治实体差异（苏联 vs. 俄罗斯、比属刚果 vs. 刚果民主共和国）只是背景，不是不同地点。

## 苏联时期和后苏联时期更名

鉴于俄罗斯/独联体指定的数量，这些是制裁工作中出现频率最高的情形。

**城市：**
- 列宁格勒（Leningrad）↔ 圣彼得堡（St. Petersburg；Sankt-Peterburg；СПб；1924 年前：Petrograd 彼得格勒，更早为圣彼得堡）
- 斯大林格勒（Stalingrad）↔ 伏尔加格勒（Volgograd）
- 高尔基（Gorky）↔ 下诺夫哥罗德（Nizhny Novgorod）
- 斯维尔德洛夫斯克（Sverdlovsk）↔ 叶卡捷琳堡（Yekaterinburg）
- 古比雪夫（Kuibyshev）↔ 萨马拉（Samara）
- 加里宁（Kalinin）↔ 特维尔（Tver）
- 谢尔盖耶夫波萨德（Sergiyev Posad）↔ 扎戈尔斯克（Zagorsk，苏联时期名称）
- 奥尔忠尼启则（Ordzhonikidze）↔ 弗拉季高加索（Vladikavkaz）
- 伏龙芝（Frunze）↔ 比什凯克（Bishkek，吉尔吉斯斯坦首都）
- 阿拉木图（Alma-Ata）↔ 阿拉木图（Almaty，哈萨克斯坦）
- 切利诺格勒（Tselinograd）↔ 阿克莫拉（Akmola）↔ 阿斯塔纳（Astana）↔ 努尔苏丹（Nur-Sultan）↔ 阿斯塔纳（Astana，哈萨克斯坦首都；多次更名）
- 阿什哈巴德（Ashkhabad）↔ 阿什哈巴德（Ashgabat，土库曼斯坦首都）
- 斯大林纳巴德（Stalinabad）↔ 杜尚别（Dushanbe，塔吉克斯坦首都）
- 蒂拉斯波尔（Tiraspol，未更名但政治地位有争议——德涅斯特河沿岸）

**国家/区域：**
- 苏联（USSR / Soviet Union）↔ 涵盖 15 个继承国（俄罗斯、乌克兰、白俄罗斯、哈萨克斯坦、乌兹别克斯坦、土库曼斯坦、塔吉克斯坦、吉尔吉斯斯坦、阿塞拜疆、亚美尼亚、格鲁吉亚、摩尔多瓦、立陶宛、拉脱维亚、爱沙尼亚）。出生地列为"USSR"并附城市时，应匹配至包含该城市的现代国家。
- 俄罗斯苏维埃联邦社会主义共和国（Russian SFSR）↔ 俄罗斯（俄罗斯联邦）
- 白俄罗斯苏维埃社会主义共和国（Belorussian SSR）↔ 白俄罗斯
- 乌克兰苏维埃社会主义共和国（Ukrainian SSR）↔ 乌克兰
- 哈萨克苏维埃社会主义共和国（Kazakh SSR）↔ 哈萨克斯坦

## 后殖民与政治性更名

**城市：**
- 孟买（Bombay）↔ 孟买（Mumbai，1995）
- 马德拉斯（Madras）↔ 金奈（Chennai，1996）
- 加尔各答（Calcutta）↔ 加尔各答（Kolkata，2001）
- 班加罗尔（Bangalore）↔ 班加罗尔（Bengaluru，2014 年官方；两者仍通用）
- 坎普尔（Cawnpore）↔ 坎普尔（Kanpur）
- 仰光（Rangoon）↔ 仰光（Yangon，缅甸；1989 年更名）
- 西贡（Saigon）↔ 胡志明市（Ho Chi Minh City，越南；1975 年更名；"Saigon"仍常用于中心城区）
- 北京（Peking）↔ 北京（Beijing，音译更新；同一城市，威妥玛拼音 vs. 汉语拼音）
- 广州（Canton）↔ 广州（Guangzhou，英语外来名 vs. 汉语拼音）
- 君士坦丁堡（Constantinople）↔ 伊斯坦布尔（Istanbul，1930 年更名，尽管伊斯坦布尔此前已在使用）
- 索尔兹伯里（Salisbury）↔ 哈拉雷（Harare，津巴布韦首都；1982 年更名）
- 洛伦索-马贵斯（Lourenço Marques）↔ 马普托（Maputo，莫桑比克首都）
- 利奥波德维尔（Leopoldville）↔ 金沙萨（Kinshasa，刚果民主共和国首都）
- 斯坦利维尔（Stanleyville）↔ 基桑加尼（Kisangani，刚果民主共和国）
- 伊丽莎白维尔（Élisabethville）↔ 卢本巴希（Lubumbashi，刚果民主共和国）
- 波斯（Persia，较老的西方外来名）↔ 伊朗（Iran，波斯于 1935 年在国际使用中更名为伊朗）

**国家：**
- 缅甸（Burma）↔ 缅甸（Myanmar，1989 年更名；美国政府多年继续使用"Burma"；筛查数据中两者均可见）
- 锡兰（Ceylon）↔ 斯里兰卡（Sri Lanka，1972）
- 罗得西亚（Rhodesia）↔ 津巴布韦（Zimbabwe，1980）
- 上沃尔特（Upper Volta）↔ 布基纳法索（Burkina Faso，1984）
- 扎伊尔（Zaire）↔ 刚果民主共和国 / DRC / 刚果（金）（1997）
- 比属刚果（Belgian Congo）↔ 刚果民主共和国（较老形式）
- 波斯（Persia）↔ 伊朗（Iran，1935 年后国际使用；"Persia"在较老文件中仍可见）
- 暹罗（Siam）↔ 泰国（Thailand，1939；曾短暂恢复；1949 年最终更名）
- 达荷美（Dahomey）↔ 贝宁（Benin，1975）
- 斯威士兰（Swaziland）↔ 埃斯瓦蒂尼（Eswatini，2018）
- 捷克斯洛伐克（Czechoslovakia）↔ 分裂为捷克共和国（现 Czechia 捷克）和斯洛伐克（1993）
- 南斯拉夫（Yugoslavia）↔ 分裂为波斯尼亚和黑塞哥维那、克罗地亚、科索沃、黑山、北马其顿、塞尔维亚、斯洛文尼亚
- 马其顿（Macedonia）↔ 北马其顿（North Macedonia，2019 年更名，在《普雷斯帕协议》之后）
- 东德 / GDR / DDR ↔ 现为德国的一部分（1990 年统一）
- 西德 / FRG ↔ 现为德国的一部分

**关于争议领土的说明：**
- 克里米亚在国际上被承认为乌克兰领土，但自 2014 年起实际由俄罗斯管理。出生地写"Crimea, Russia"与"Crimea, Ukraine"指的是同一领土，只是政治主张有争议。
- 台湾 / 中华民国 vs. 中华人民共和国：在筛查实践中为不同司法辖区。不得等同。
- 朝鲜 / DPRK 和韩国 / ROK：不同司法辖区。不得等同。
- 西撒哈拉：摩洛哥与阿拉伯撒哈拉民主共和国（SADR）之间存在争议。

## 中东和北非主要对应

- 麦加（Mecca）↔ 麦加（Makkah，音译变体——同一城市）
- 麦地那（Medina）↔ 麦地那（Madinah）
- 吉达（Jeddah）↔ 吉达（Jiddah）↔ 吉达（Jedda）
- 大马士革（Damascus）↔ 大马士革（Dimashq，阿拉伯语）↔ 沙姆（Sham，区域名称）
- 阿勒颇（Aleppo）↔ 阿勒颇（Halab）
- 开罗（Cairo）↔ 开罗（Al-Qahirah，阿拉伯语）
- 亚历山大（Alexandria）↔ 亚历山大（Al-Iskandariyah）
- 德黑兰（Tehran）↔ 德黑兰（Teheran，较老拼写；同一城市）
- 巴格达（Baghdad）↔ 巴格达（Baghdād）
- 摩苏尔（Mosul）↔ 摩苏尔（Al-Mawsil）
- 的黎波里（Tripoli，利比亚）vs. 的黎波里（Tripoli，黎巴嫩）——两个不同城市；绝不等同

## 东亚主要对应

- 北京（Beijing）↔ 北平（Peking）↔ 北平（Beiping，1928-1949 年名称）——同一城市
- 南京（Nanjing）↔ 南京（Nanking）——同一城市
- 重庆（Chongqing）↔ 重庆（Chungking）——同一城市
- 天津（Tianjin）↔ 天津（Tientsin）——同一城市
- 香港（Hong Kong）↔ 香港 ↔ 香港（Xianggang，汉语拼音）——同一城市
- 澳门（Macau）↔ 澳门（Macao）↔ 澳门（Aomen，汉语拼音）——同一城市
- 平壤（Pyongyang）↔ 平壤（P'yŏngyang，马科恩-赖肖尔转写）
- 首尔（Seoul）↔ 首尔（서울，韩语）——无拉丁变体；汉字形式京城是殖民时期名称"Keijō"，同一城市
- 孟买（Mumbai，已见上文）

## 撒哈拉以南非洲对应

- 除上述国家级更名外：
- 科特迪瓦（Côte d'Ivoire）↔ 象牙海岸（Ivory Coast，1985 年起官方在一切语言中使用"Côte d'Ivoire"，但"Ivory Coast"在英语来源中仍常见）
- 佛得角（Cape Verde）↔ 佛得角（Cabo Verde，该国自 2013 年起官方使用"Cabo Verde"）
- 埃斯瓦蒂尼（Eswatini）↔ 斯威士兰（Swaziland，已见上文）

## 如何应用本参考文件

**在第 0 层解析：** 摄入出生地或地址字段时，同时记录所提供的字面值和规范化形式。规范化保留原文；替代名称并列保留。

示例：清单条目出生地 = "Leningrad, USSR"；规范化形式 = "Leningrad" + 替代名称"St. Petersburg" + 国家 = 俄罗斯（通过继承国映射）。

**在第 2 层 TP-2：** 一方任一名称与另一方任一名称匹配即满足出生地匹配。被筛查方出生地"St. Petersburg, Russia"与清单方出生地"Leningrad, USSR"产生 TP-2 市级匹配。

**在第 3 层研究：** 构建包含地名的检索查询时，先尝试现代名称（搜索引擎覆盖更广），如清单条目使用历史形式则以历史名称作为回退。旧档案来源可能只索引历史名称。

## 有疑问时

如地名对应不在本参考文件中，但你有理由相信两个名称指同一地点，应将对应关系视为未核验，并将出生地匹配从"市级"降级为"如适用则国家级，否则升级"。不得凭空捏造对应关系。保守姿态：漏掉一个对应关系将案件送往升级；捏造的对应关系会产生虚假 TP（更糟）。

## 局限

这不是地名录。它涵盖因苏联、后殖民和亚洲主要更名事件而最可能在筛查裁定中出现的对应关系。较少见的对应关系——村级更名、次要重组、较少见语言中的其他外来名——应在它们重要时于第 3 层查阅，而非在此记忆。
