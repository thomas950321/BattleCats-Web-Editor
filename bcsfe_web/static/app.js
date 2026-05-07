document.addEventListener('DOMContentLoaded', () => {
    // ── 頁面載入時，顯示上次保存的帳號 ID ──────────────────────────
    (function restoreSavedInquiry() {
        const saved = localStorage.getItem('last_inquiry_code');
        if (!saved) return;
        const container = document.getElementById('savedInquirySection');
        const display  = document.getElementById('savedInquiryCode');
        if (container && display) {
            display.textContent = saved;
            container.classList.remove('hidden');
        }
        // 綁定登入頁的複製按鈕
        const btnCopy = document.getElementById('btnCopySavedInquiry');
        if (btnCopy) {
            btnCopy.addEventListener('click', () => {
                navigator.clipboard.writeText(saved).then(() => {
                    btnCopy.textContent = '✅ 已複製！';
                    setTimeout(() => { btnCopy.textContent = '複製'; }, 2000);
                });
            });
        }
    })();

    // ── 頁面載入時，自動填回上次的引繼碼（讓「返回登入頁面」後免手動輸入）──
    (function autoFillLastCodes() {
        const lastTC = localStorage.getItem('last_transfer_code');
        const lastCC = localStorage.getItem('last_conf_code');
        if (!lastTC || !lastCC) return;
        const tcEl = document.getElementById('transferCode');
        const ccEl = document.getElementById('confCode');
        if (tcEl) tcEl.value = lastTC;
        if (ccEl) ccEl.value = lastCC;
    })();
    // 元素引用
    const loginPanel = document.getElementById('login-panel');
    const dashboard = document.getElementById('dashboard');
    const resultPanel = document.getElementById('result-panel');
    const btnLogin = document.getElementById('btnLogin');
    const btnClone = document.getElementById('btnClone');
    const btnUpload = document.getElementById('btnUpload');
    const btnCopyInquiry = document.getElementById('btnCopyInquiry');
    const btnRestart = document.getElementById('btnRestart');
    const notification = document.getElementById('notification');
    const resTransferCode = document.getElementById('resTransferCode');
    const resConfCode = document.getElementById('resConfCode');
    const inquiryCodeDisplay = document.getElementById('inquiryCodeDisplay');
    // 用於顯示結果面板的元素
    const resultTitle = document.getElementById('resultTitle');
    const resultWarning = document.getElementById('resultWarning');
    const originalAccountSection = document.getElementById('originalAccountSection');
    const cloneAccountLabel = document.getElementById('cloneAccountLabel');
    const origTransferCode = document.getElementById('origTransferCode');
    const origConfCode = document.getElementById('origConfCode');
    const labelNewTC = document.getElementById('labelNewTC');
    const labelNewCC = document.getElementById('labelNewCC');

    // 輿模式切換：重置結果面板為普通上傳模式
    function setResultMode(isClone) {
        if (isClone) {
            resultTitle.textContent = '帳號複製成功！';
            resultWarning.textContent = '請妥善保存以下兩組代碼，原帳与複製帳均可登入遊戲。';
            originalAccountSection.classList.remove('hidden');
            cloneAccountLabel.classList.remove('hidden');
            labelNewTC.textContent = '引繼碼 (Transfer Code)';
            labelNewCC.textContent = '認證碼 (Confirmation Code)';
        } else {
            resultTitle.textContent = '存檔上傳成功！';
            resultWarning.textContent = '請務必記下並妥善保存下列資訊，原有的引繼碼已失效。';
            originalAccountSection.classList.add('hidden');
            cloneAccountLabel.classList.add('hidden');
            labelNewTC.textContent = '新引繼碼 (New Transfer Code)';
            labelNewCC.textContent = '新認證碼 (New Confirmation Code)';
        }
    }

    // 狀態切換 - 通知
    function showNotification(message, type = 'success') {
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.remove('hidden');
        clearTimeout(notification._t);
        notification._t = setTimeout(() => notification.classList.add('hidden'), 3000);
    }

    // 自動 Clamp (防止過大數值)
    document.addEventListener('change', e => {
        const el = e.target;
        if (el.type !== 'number' || el.value === '') return;
        const max = parseInt(el.max);
        const min = parseInt(el.min) || 0;
        const val = parseInt(el.value);
        if (!isNaN(max) && val > max) {
            el.value = max;
            showNotification(`已自動修正為上限 ${max.toLocaleString()}`, 'warn');
        } else if (val < min) {
            el.value = min;
        }
    });

    // 複製功能
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const text = document.getElementById(targetId).textContent;
            navigator.clipboard.writeText(text).then(() => {
                showNotification('已複製到剪貼簿！', 'success');
            });
        });
    });

    // 複製帳號（完整複製：兩次登入+兩次上傳）
    btnClone.addEventListener('click', async () => {
        const transferCode = document.getElementById('transferCode').value.trim();
        const confCode     = document.getElementById('confCode').value.trim();
        const countryCode  = document.getElementById('countryCode').value;
        const gameVersion  = document.getElementById('gameVersion').value.trim();

        if (!transferCode || !confCode) {
            showNotification('請先輸入引繼碼與認證碼', 'error');
            return;
        }

        btnClone.disabled = true;
        btnClone.textContent = '🔄 複製中（約需 15–30 秒）...';

        try {
            // 一個請求搞定：後端執行兩次登入+兩次上傳
            const res = await fetch('/save/clone', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    transfer_code: transferCode,
                    confirmation_code: confCode,
                    country_code: countryCode,
                    game_version: gameVersion
                })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '複製失敗');

            // 存入 localStorage（以原帳新代碼為主）
            localStorage.setItem('last_transfer_code', data.original_transfer_code);
            localStorage.setItem('last_conf_code',     data.original_confirmation_code);

            // 設定複製模式，填入兩組代碼
            setResultMode(true);
            origTransferCode.textContent = data.original_transfer_code;
            origConfCode.textContent     = data.original_confirmation_code;
            resTransferCode.textContent  = data.clone_transfer_code;
            resConfCode.textContent      = data.clone_confirmation_code;

            loginPanel.classList.add('hidden');
            resultPanel.classList.remove('hidden');
            showNotification('複製完成！兩組帳密已顯示。', 'success');

        } catch (err) {
            showNotification(err.message || '複製失敗', 'error');
        } finally {
            btnClone.disabled = false;
            btnClone.textContent = '🐱 複製帳號（一鍵產生兩組帳密）';
        }
    });


    // 返回登入時，重置結果面板到一般模式
    btnRestart.addEventListener('click', () => {
        setResultMode(false);
        location.reload();
    });

    // 分頁切換
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;

            // 按鈕狀態
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // 內容狀態
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
                content.classList.remove('active');
            });
            const targetContent = document.getElementById(target);
            if (targetContent) {
                targetContent.classList.remove('hidden');
                targetContent.classList.add('active');
            }
        });
    });

    // 項目名稱映射
    const itemNames = {
        '戰鬥道具': ['加速', '寶物雷達', '土豪貓', '貓咪電腦', '洞悉先機', '狙擊手'],
        '喵力達': ['喵力達【A】', '喵力達【B】', '喵力達【C】'],
        '貓眼石': ['EX', '稀有', '激稀有', '超激稀有', '傳說', '闇'],
        '基地素材': ['紅磚', '羽毛', '備長炭', '鋼製齒輪', '黃金', '宇宙石', '神祕骨頭', '菊石'],
        '貓薄荷': [
            '紫色薄荷種子', '紅色薄荷種子', '藍色薄荷種子', '綠色薄荷種子', '黃色薄荷種子',
            '紫色貓薄荷', '紅色貓薄荷', '藍色貓薄荷', '綠色貓薄荷', '黃色貓薄荷',
            '彩虹貓薄荷',
            '古代貓薄荷種子',
            '古代貓薄荷',
            '彩虹貓薄荷種子',
            '黃金貓薄荷',
            '惡魔貓薄荷種子',
            '惡魔貓薄荷',
            '黃金貓薄荷種子',
            '紫獸石',
            '紅獸石',
            '藍獸石',
            '綠獸石',
            '黃獸石',
            '彩虹獸石',
            '紫獸結晶',
            '紅獸結晶',
            '藍獸結晶',
            '綠獸結晶',
            '黃獸結晶'
        ]
    };

    // 輔助函式：生成動態網格 (使用新版 .flex-item 結構)
    function generateGrid(containerId, data, prefix) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';
        
        // 安全檢查：確保 data 是數組，避免流程崩潰
        if (!Array.isArray(data)) {
            console.warn(`[Render] ${prefix} 數據為空或非數組格式`);
            data = [];
        }

        const maxLimit = (prefix === '貓薄荷' || prefix === '本能玉') ? 998 : 9999;
        
        data.forEach((val, i) => {
            const item = document.createElement('div');
            item.className = 'flex-item';
            
            let name = '';
            let amount = val;
            let id = i;
            if (typeof val === 'object' && val !== null) {
                name = val.name;
                amount = val.amount;
                id = val.id;
            } else {
                name = (itemNames[prefix] && itemNames[prefix][i]) ? itemNames[prefix][i] : `${prefix} ${i + 1}`;
            }

            item.innerHTML = `
                <label>${name}</label>
                <input type="number" class="${prefix}-input" data-index="${id}" value="${amount}" min="0" max="${maxLimit}" placeholder="0">
            `;
            container.appendChild(item);
        });
    }

    // 登入讀取
    btnLogin.addEventListener('click', async () => {
        btnLogin.disabled = true;
        btnLogin.textContent = '讀取中...';

        const payload = {
            transfer_code: document.getElementById('transferCode').value.trim(),
            confirmation_code: document.getElementById('confCode').value.trim(),
            country_code: document.getElementById('countryCode').value,
            game_version: document.getElementById('gameVersion').value.trim()
        };

        if (!payload.transfer_code || !payload.confirmation_code) {
            showNotification('請輸入完整的引擬資訊', 'error');
            btnLogin.disabled = false;
            btnLogin.textContent = '下載並讀取存檔';
            return;
        }

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();

            if (result.status === 'success') {
                showNotification('存檔讀取成功！');
                loginPanel.classList.add('hidden');
                dashboard.classList.remove('hidden');

                // 抓取真實數據
                const saveDataRes = await fetch('/save/get');
                if (!saveDataRes.ok) throw new Error('無法獲取存檔詳細數據');
                const saveData = await saveDataRes.json();
                window.lastSaveData = JSON.parse(JSON.stringify(saveData)); // 拍攝初始快照

                // 基礎物資
                document.getElementById('catfood').value = saveData.catfood;
                document.getElementById('xp').value = saveData.xp;
                document.getElementById('np').value = saveData.np || 0;
                document.getElementById('leadership').value = saveData.leadership || 0;

                // 扭蛋券
                document.getElementById('normalTickets').value = saveData.normal_tickets;
                document.getElementById('rareTickets').value = saveData.rare_tickets;
                document.getElementById('platinumTickets').value = saveData.platinum_tickets;
                document.getElementById('legendTickets').value = saveData.legend_tickets;
                document.getElementById('platinumShards').value = saveData.platinum_shards || 0;

                // 其他
                generateGrid('talent-orbs-grid', saveData.talent_orbs || [], '本能玉');
                generateGrid('labyrinthMedalsGrid', saveData.labyrinth_medals || [], '迷宮獎牌');
                document.getElementById('playTime').value = saveData.play_time || 0;

                // 動態生成素材列表 (增加安全回退值)
                generateGrid('battle-items-grid', saveData.battle_items || [], '戰鬥道具');
                generateGrid('catamins-grid', saveData.catamins || [], '喵力達');
                generateGrid('catseyes-grid', saveData.catseyes || [], '貓眼石');
                generateGrid('catfruit-grid', saveData.catfruit || [], '貓薄荷');
                generateGrid('base-materials-grid', saveData.base_materials || [], '基地素材');

                document.getElementById('inquiryCodeDisplay').textContent = `ID: ${saveData.inquiry_code || 'N/A'}`;
            } else {
                showNotification('讀取失敗: ' + (result.detail || '碼錯誤或連線失敗'), 'error');
            }
        } catch (err) {
            console.error(err);
            showNotification('操作失敗: ' + err.message, 'error');
        } finally {
            btnLogin.disabled = false;
            btnLogin.textContent = '下載並讀取存檔';
        }
    });

    // 儲存並上傳
    btnUpload.addEventListener('click', async () => {
        if (!window.lastSaveData) return;
        btnUpload.disabled = true;
        btnUpload.textContent = '計算差異中...';

        try {
            const getListValues = (selector) => {
                return Array.from(document.querySelectorAll(selector))
                    .sort((a, b) => a.dataset.index - b.dataset.index)
                    .map(input => parseInt(input.value) || 0);
            };

            const getListMap = (selector) => {
                const map = {};
                document.querySelectorAll(selector).forEach(input => {
                    map[input.dataset.index] = parseInt(input.value) || 0;
                });
                return map;
            };

            // 核心：比對差異 (Dirty Check)
            const updates = {};
            const itemIds = [
                ['catfood', 'catfood'], ['xp', 'xp'], ['np', 'np'], 
                ['leadership', 'leadership'], ['normalTickets', 'normal_tickets'], 
                ['rareTickets', 'rare_tickets'], ['platinumTickets', 'platinum_tickets'], 
                ['legendTickets', 'legend_tickets'], ['platinumShards', 'platinum_shards'], 
                ['playTime', 'play_time']
            ];

            // 1. 比對基礎數值 (增加安全檢查)
            itemIds.forEach(([domId, saveKey]) => {
                const el = document.getElementById(domId);
                if (el) {
                    const val = parseInt(el.value) || 0;
                    if (val !== window.lastSaveData[saveKey]) {
                        updates[saveKey] = val;
                    }
                }
            });

            // 2. 比對列表類 (數組)
            const listGrids = {
                battle_items: '.戰鬥道具-input',
                catamins: '.喵力達-input',
                catseyes: '.貓眼石-input',
                catfruit: '.貓薄荷-input',
                base_materials: '.基地素材-input',
                labyrinth_medals: '.迷宮獎牌-input'
            };

            for (const [key, selector] of Object.entries(listGrids)) {
                const currentList = getListValues(selector);
                const originalList = window.lastSaveData[key] || [];
                if (JSON.stringify(currentList) !== JSON.stringify(originalList)) {
                    updates[key] = currentList;
                }
            }

            // 3. 比對本能珠 (字典)
            const currentOrbs = getListMap('.本能玉-input');
            const originalOrbs = {};
            (window.lastSaveData.talent_orbs || []).forEach(o => originalOrbs[o.id] = o.amount);
            if (JSON.stringify(currentOrbs) !== JSON.stringify(originalOrbs)) {
                updates.talent_orbs = currentOrbs;
            }

            const payload = {
                items: updates,
                stages: {
                    clear_tutorial: document.getElementById('clearTutorial')?.checked || false,
                    clear_world: document.getElementById('clearWorld')?.checked || false,
                    clear_future: document.getElementById('clearFuture')?.checked || false,
                    clear_cosmos: document.getElementById('clearCosmos')?.checked || false,
                    clear_aku: document.getElementById('clearAku')?.checked || false,
                    max_treasures_world: document.getElementById('advMaxTreasuresWorld')?.checked || false,
                    max_treasures_future: document.getElementById('advMaxTreasuresFuture')?.checked || false,
                    max_treasures_cosmos: document.getElementById('advMaxTreasuresCosmos')?.checked || false,
                    unlock_medals: document.getElementById('advUnlockMedals')?.checked || false
                },
                advanced: {
                    cats: {
                        unlock_all: document.getElementById('advUnlockAll')?.checked || false,
                        max_level: document.getElementById('advMaxLevel')?.checked || false,
                        true_form: document.getElementById('advTrueForm')?.checked || false,
                        fourth_form: document.getElementById('advFourthForm')?.checked || false,
                        max_talents: document.getElementById('advMaxTalents')?.checked || false
                    },
                    tech: {
                        max_all_tech: document.getElementById('advMaxTech')?.checked || false
                    },
                    progress: {
                        max_gamatoto: document.getElementById('advMaxGamatoto')?.checked || false,
                        best_gamatoto_members: document.getElementById('advBestMembers')?.checked || false,
                    },
                }
            };

            // 第一步：套用修改
            btnUpload.textContent = '正在通訊...';
            const patchResp = await fetch('/save/patch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!patchResp.ok) {
                const errData = await patchResp.json();
                throw new Error(errData.detail || '套用修改失敗');
            }

            // 第二步：執行上傳
            showNotification('正在上傳至遊戲伺服器...');
            const uploadResp = await fetch('/save/upload', { method: 'POST' });
            if (!uploadResp.ok) {
                const errData = await uploadResp.json();
                throw new Error(errData.detail || '伺服器上傳失敗');
            }

            const result = await uploadResp.json();

            if (result.status === 'success') {
                dashboard.classList.add('hidden');
                resultPanel.classList.remove('hidden');
                resTransferCode.textContent = result.new_transfer_code;
                resConfCode.textContent = result.new_confirmation_code;
                
                // 保存至本地瀏覽器，防止刷新遺失
                localStorage.setItem('last_transfer_code', result.new_transfer_code);
                localStorage.setItem('last_conf_code', result.new_confirmation_code);
                
                showNotification('上傳成功！請保存新碼。');
            }
        } catch (err) {
            showNotification(err.message || '操作過程發生錯誤', 'error');
        } finally {
            btnUpload.disabled = false;
            btnUpload.textContent = '儲存並上傳至伺服器';
        }
    });

    // 找回上次代碼
    document.getElementById('btnRecoverLastCode').addEventListener('click', () => {
        const lastTC = localStorage.getItem('last_transfer_code');
        const lastCC = localStorage.getItem('last_conf_code');
        
        if (lastTC && lastCC) {
            document.getElementById('transferCode').value = lastTC;
            document.getElementById('confCode').value = lastCC;
            showNotification('已還原上次上傳成功的代碼！');
        } else {
            showNotification('未找到任何本地存檔代碼紀錄。', 'error');
        }
    });

    // 複製帳號 ID（同時存入 localStorage 讓頁面重整後仍可查閱）
    btnCopyInquiry.addEventListener('click', () => {
        const raw = inquiryCodeDisplay.textContent || '';
        const code = raw.replace(/^ID:\s*/, '').trim();
        if (!code || code === '-----' || code === 'N/A') {
            showNotification('尚未登入，無帳號 ID 可複製', 'error');
            return;
        }
        // 寫入 localStorage
        localStorage.setItem('last_inquiry_code', code);
        // 即時更新登入頁面的顯示區塊
        const container = document.getElementById('savedInquirySection');
        const display   = document.getElementById('savedInquiryCode');
        if (container && display) {
            display.textContent = code;
            container.classList.remove('hidden');
        }
        navigator.clipboard.writeText(code).then(() => {
            showNotification(`帳號 ID 已複製並儲存：${code}`, 'success');
            btnCopyInquiry.textContent = '✅ 已複製！';
            setTimeout(() => { btnCopyInquiry.textContent = '📋 複製帳號 ID'; }, 2000);
        }).catch(() => {
            showNotification('複製失敗，請手動選取', 'error');
        });
    });

    // 移植帳號按鈕
    document.getElementById('btnTransplant').addEventListener('click', async () => {
        const srcTC = document.getElementById('srcTC').value.trim();
        const srcCC = document.getElementById('srcCC').value.trim();
        const dstTC = document.getElementById('dstTC').value.trim();
        const dstCC = document.getElementById('dstCC').value.trim();
        const cc    = document.getElementById('countryCode').value;
        const gv    = document.getElementById('gameVersion').value.trim();

        if (!srcTC || !srcCC || !dstTC || !dstCC) {
            showNotification('請填寫來源帳與目標帳的完整代碼', 'error');
            return;
        }

        const btn = document.getElementById('btnTransplant');
        btn.disabled = true;
        btn.textContent = '🔄 移植中（約需 20–40 秒）...';

        try {
            const res = await fetch('/save/transplant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_transfer_code: srcTC,
                    source_confirmation_code: srcCC,
                    target_transfer_code: dstTC,
                    target_confirmation_code: dstCC,
                    country_code: cc,
                    game_version: gv,
                })
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || '移植失敗');

            localStorage.setItem('last_transfer_code', data.new_transfer_code);
            localStorage.setItem('last_conf_code',     data.new_confirmation_code);

            // 一般模式：只顯示目標帳的新代碼（移植成功）
            setResultMode(false);
            document.getElementById('resultTitle').textContent   = '移植成功！';
            document.getElementById('resultWarning').textContent = '空殼帳號已注入強帳進度，以下是新的引繼代碼。';
            resTransferCode.textContent = data.new_transfer_code;
            resConfCode.textContent     = data.new_confirmation_code;

            loginPanel.classList.add('hidden');
            resultPanel.classList.remove('hidden');
            showNotification('移植完成！空殼帳現在擁有強帳進度。', 'success');

        } catch (err) {
            showNotification(err.message || '移植失敗', 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = '🚀 開始移植';
        }
    });
});
