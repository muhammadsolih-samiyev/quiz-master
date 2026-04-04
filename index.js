const { Telegraf, session, Markup } = require('telegraf');
const mongoose = require('mongoose');
const http = require('http');
const { translate } = require('google-translate-api-x');

// ⚠️ Security Note: Consider moving tokens to a .env file in production!
const bot = new Telegraf('8539493439:AAFn20XbwTRQ2VxMhqo7-OvceViqPNxjAII');
const MONGO_URI = 'mongodb+srv://btwimbennet_db_user:ApplePie22@cluster0.ai4welu.mongodb.net/?appName=Cluster0';

bot.use(session());
bot.use((ctx, next) => {
    ctx.session = ctx.session || {};
    return next();
});

// ==========================================
// 0. DATABASES & GLOBAL STATE
// ==========================================
const SUPER_ADMINS = ['wemxy'];
const adminsDB = new Set();
const requiredChannels = new Set(['@QuizzingTashkent']);
const globalTestsDB = {};
const userTestsDB = {};
const userProfiles = {};

const activeMatches = {};
const pollTracker = {};

const generateId = () => Math.random().toString(36).substr(2, 6);
const isGroup = (ctx) => ['group', 'supergroup'].includes(ctx.chat?.type);

const isAnyAdmin = (username) => {
    if (!username) return false;
    const lowerUser = username.toLowerCase();
    if (SUPER_ADMINS.some(a => a.toLowerCase() === lowerUser)) return true;
    for (let admin of adminsDB) {
        if (admin.toLowerCase() === lowerUser) return true;
    }
    return false;
};

const DataSchema = new mongoose.Schema({
    id: { type: String, default: 'main' },
    globalTests: { type: Object, default: {} },
    userTests: { type: Object, default: {} },
    profiles: { type: Object, default: {} },
    admins: { type: Array, default: [] },
    channels: { type: Array, default: ['@QuizzingTashkent'] }
}, { minimize: false });
const DataStore = mongoose.model('DataStore', DataSchema);

async function backupData() {
    try {
        await DataStore.findOneAndUpdate({ id: 'main' }, {
            globalTests: globalTestsDB,
            userTests: userTestsDB,
            profiles: userProfiles,
            admins: Array.from(adminsDB),
            channels: Array.from(requiredChannels)
        }, { upsert: true });
    } catch (e) { console.error("💾 Backup Xatosi:", e.message); }
}

const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

async function translateText(text, targetLanguage) {
    try {
        const res = await translate(text, { to: targetLanguage });
        return res.text || text;
    } catch (error) { return text; }
}

// ==========================================
// 1. CRASH PROTECTORS
// ==========================================
bot.catch((err, ctx) => console.error(`[Xato] ${ctx.updateType}:`, err.message));
process.on('uncaughtException', err => console.error('[Fatal]', err.message));
process.on('unhandledRejection', err => console.error('[Promise]', err.message));

// ==========================================
// 2. FORCED SUBSCRIPTION LOGIC
// ==========================================
async function isUserSubbed(ctx) {
    if (isAnyAdmin(ctx.from?.username)) return true;
    if (requiredChannels.size === 0) return true;
    for (const ch of requiredChannels) {
        try {
            const member = await ctx.telegram.getChatMember(ch, ctx.from.id);
            if (!['member', 'administrator', 'creator'].includes(member.status)) return false;
        } catch (e) { return false; }
    }
    return true;
}

function getJoinKeyboard() {
    const btns = Array.from(requiredChannels).map(ch => [Markup.button.url(`📢 A'zo bo'lish: ${ch}`, `https://t.me/${ch.replace('@', '')}`)]);
    btns.push([Markup.button.callback('🔄 Tasdiqlash', 'verify_sub')]);
    return Markup.inlineKeyboard(btns);
}

bot.action('verify_sub', async (ctx) => {
    if (await isUserSubbed(ctx)) {
        ctx.deleteMessage().catch(() => { });
        return ctx.reply("✅ Tasdiqlandi! Xush kelibsiz.", getMainMenu(ctx));
    }
    return ctx.answerCbQuery("❌ Iltimos, barcha kanallarga a'zo bo'ling!", { show_alert: true });
});

// ==========================================
// 3. UI TRANSLATIONS & COMPACT MENUS
// ==========================================
const translations = {
    'Uzbek': {
        global: '📝 Umumiy Testlar', private: '📁 Mening testlarim', lang_btn: '🌐 Tilni o\'zgartirish', prof: '👤 Profilim', admin_btn: '🔑 ADMIN PANEL',
        create: '➕ Yaratish', play: '▶️ O\'ynash', share: '🏟️ Guruhga yuborish', trans: '🔤 Tarjima', add_poll: '➕ Savol qo\'shish', del: '🗑️ O\'chirish'
    },
    'English': {
        global: '📝 Global Tests', private: '📁 My Tests', lang_btn: '🌐 Language', prof: '👤 Profile', admin_btn: '🔑 ADMIN PANEL',
        create: '➕ Create', play: '▶️ Play', share: '🏟️ Host Group', trans: '🔤 Translate', add_poll: '➕ Add Poll', del: '🗑️ Delete'
    },
    'Russian': {
        global: '📝 Общие тесты', private: '📁 Мои тесты', lang_btn: '🌐 Язык', prof: '👤 Профиль', admin_btn: '🔑 ПАНЕЛЬ АДМИНА',
        create: '➕ Создать', play: '▶️ Играть', share: '🏟️ В группе', trans: '🔤 Перевести', add_poll: '➕ Добавить', del: '🗑️ Удалить'
    }
};

function getMainMenu(ctx) {
    const lang = userProfiles[ctx.from.id]?.lang || 'Uzbek';
    const t = translations[lang];
    const keyboard = [[t.global, t.private], [t.prof, t.lang_btn]];
    if (isAnyAdmin(ctx.from?.username)) keyboard.push([t.admin_btn]);
    return Markup.keyboard(keyboard).resize();
}

const globalText = `♻️ **Testlar** - Bu bilimingizni quiz orqali sinab ko'rish va o'rganishga yordam beradigan xizmat.
📚 **Siz quyidagilardan foydalanishingiz mumkin:**
• Botga avvaldan qo'shilgan umumiy testlardan
• O'zingiz yaratgan shaxsiy testlardan
• Guruhlarda va shaxsiy chatlarda do'stlar bilan bellashish

⏳ Quyidagi ro'yxatdan o'zingizga kerakli testni tanlang va boshlang!`;
const myText = `📋 **Mening testlarim:**\n\nQuyidagi ro'yxatdan o'z testlaringizni tanlashingiz mumkin:`;

// ==========================================
// 4. CORE QUIZ HELPERS (COUNTDOWN & RESULTS)
// ==========================================

// Teskari sanoq tizimi
async function showCountdown(ctx, title) {
    try {
        const msg = await ctx.reply(`⏳ **Boshlanmoqda:** ${title}\n\n5`, { parse_mode: 'Markdown' });
        for (let i = 4; i >= 1; i--) {
            await sleep(1000);
            await ctx.telegram.editMessageText(
                ctx.chat.id, msg.message_id, undefined, 
                `⏳ **Boshlanmoqda:** ${title}\n\n${i}`, 
                { parse_mode: 'Markdown' }
            ).catch(() => {});
        }
        await sleep(1000);
        await ctx.telegram.deleteMessage(ctx.chat.id, msg.message_id).catch(() => {});
    } catch (e) { console.error("Countdown xatosi:", e.message); }
}

async function sendResults(matchId, ctx) {
    const m = activeMatches[matchId];
    if (!m) return;

    let res = `🏁 **'${m.test.title}'** testi yakunlandi!\n\n`;
    const sorted = Array.from(m.players).sort((a, b) => (m.scores[b] || 0) - (m.scores[a] || 0) || (m.times[a] || 0) - (m.times[b] || 0));
    const total = m.test.questions.length;

    if (m.isSolo) {
        const uid = Array.from(m.players)[0];
        const score = m.scores[uid] || 0;
        const answered = m.answered ? (m.answered[uid] || 0) : 0;
        const time = m.times[uid] || 0;
        
        const incorrect = answered > score ? answered - score : 0;
        const missed = total > answered ? total - answered : 0;
        const percent = total > 0 ? Math.round((score / total) * 100) : 0;

        let emoji = percent >= 80 ? '🏆' : percent >= 50 ? '👍' : '💪';
        
        res += `👤 **Ishtirokchi:** ${m.usernames[uid]}\n\n`;
        res += `📊 **Umumiy savollar:** ${total} ta\n`;
        res += `✅ **To'g'ri javoblar:** ${score} ta\n`;
        if (incorrect > 0) res += `❌ **Xato javoblar:** ${incorrect} ta\n`;
        if (missed > 0) res += `⚠️ **Javob berilmagan:** ${missed} ta\n`;
        res += `⏱ **Sarflangan vaqt:** ${time.toFixed(1)} soniya\n`;
        res += `📈 **Natija (Foiz):** ${percent}%\n\n`;
        res += `${emoji} Ajoyib ko'rsatkich! Ushbu testni do'stlaringiz bilan ham ulashing.`;
    } else {
        res += `📝 _${total} ta savol_\n\n`;
        if (sorted.length === 0 || !m.answered || Object.keys(m.answered).length === 0) {
            res += "Hech kim ishtirok etmadi.\n";
        } else {
            sorted.forEach((uid, i) => {
                if ((m.answered[uid] || 0) > 0) {
                    let medal = i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : "🏅";
                    let score = m.scores[uid] || 0;
                    let time = m.times[uid] || 0;
                    let percent = total > 0 ? Math.round((score / total) * 100) : 0;
                    res += `${medal} ${m.usernames[uid]} – **${score}** ta to'g'ri (${time.toFixed(1)} sek, ${percent}%)\n`;
                }
            });
        }
        res += `\n🏆 G'oliblarni tabriklaymiz!`;
    }

    const shareUrl = `https://t.me/${ctx.botInfo.username}?startgroup=match_${m.test.id}_t${m.timer}`;

    delete activeMatches[matchId];
    for (let pid in pollTracker) { if (pollTracker[pid].matchId === matchId) delete pollTracker[pid]; }

    return ctx.reply(res, {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard([[Markup.button.url('↗️ Do\'stlarga ulashish', shareUrl)]])
    });
}

async function startQuiz(matchId, ctx) {
    const m = activeMatches[matchId];
    if (!m || m.status !== 'lobby') return;

    m.status = 'playing';
    await showCountdown(ctx, m.test.title);

    for (let i = 0; i < m.test.questions.length; i++) {
        m.questionStart = Date.now();
        const q = m.test.questions[i];
        const timeLimit = m.timer > 0 ? m.timer : 30;
        const correctOptId = Number(q.correct_option_id) || 0;

        try {
            const pollMsg = await ctx.telegram.sendPoll(
                ctx.chat.id,
                `[${i + 1}/${m.test.questions.length}] ${q.question}`,
                q.options.map(o => o.text),
                { 
                    type: 'quiz', 
                    correct_option_id: correctOptId, 
                    is_anonymous: false, 
                    open_period: timeLimit 
                }
            );
            
            pollTracker[pollMsg.poll.id] = { 
                matchId: matchId, 
                correctOpt: correctOptId,
                answeredUsers: new Set() // Takroriy javob oldini olish
            };
        } catch (e) { console.error("Poll error:", e.message); }

        await sleep((timeLimit * 1000) + 1500);
    }

    await sendResults(matchId, ctx);
}

async function autoStartIfReady(matchId, ctx) {
    const m = activeMatches[matchId];
    if (!m || m.status !== 'lobby') return;
    if (m.players.size >= 2) {
        await ctx.editMessageText(`🚀 **O'yin boshlanmoqda!** (Barcha o'yinchilar tayyor)`).catch(() => { });
        await startQuiz(matchId, ctx);
    }
}

// ==========================================
// 5. START & LOBBY ROUTING
// ==========================================
bot.start(async (ctx) => {
    const payload = ctx.startPayload;
    if (!userProfiles[ctx.from.id]) { userProfiles[ctx.from.id] = { lang: 'Uzbek' }; backupData(); }

    if (isGroup(ctx)) {
        if (!payload || !payload.startsWith('match_')) return; 

        const parts = payload.split('_t');
        const testId = parts[0].replace('match_', '');
        const timeLimit = parseInt(parts[1]) || 15;
        const test = userTestsDB[testId] || globalTestsDB[testId];

        if (!test) return ctx.reply("❌ Test topilmadi / o'chirilgan.");

        const matchId = generateId();
        activeMatches[matchId] = {
            hostId: Number(ctx.from.id), test: test, players: new Set(),
            scores: {}, usernames: {}, times: {}, answered: {},
            timer: timeLimit, status: 'lobby', questionStart: 0, isSolo: false
        };

        return ctx.reply(`🎲 **${test.title}**\n\n🗡 Savollar soni: ${test.questions.length}\n⏱ Vaqt: ${timeLimit > 0 ? timeLimit + ' soniya' : 'Cheksiz (30s)'}\n\n🏁 Boshlash uchun kamida 2 kishi tayyor bo'lishi kerak.`,
            Markup.inlineKeyboard([[Markup.button.callback('✋ Men tayyorman!', `join|${matchId}`)]]));
    }

    if (!(await isUserSubbed(ctx))) return ctx.reply("♻️ Botdan foydalanish uchun kanallarga a'zo bo'ling:", getJoinKeyboard());
    return ctx.reply("👋 Xush kelibsiz! Menuni tanlang:", getMainMenu(ctx));
});

// ==========================================
// 6. SMART NAVIGATION REDIRECTS (PRIVATE ONLY)
// ==========================================
bot.on('text', async (ctx, next) => {
    if (isGroup(ctx) || ctx.session.step) return next();

    let key = null;
    const lang = userProfiles[ctx.from.id]?.lang || 'Uzbek';
    const t = translations[lang];
    for (const l in translations) { for (const k in translations[l]) { if (translations[l][k] === ctx.message.text) key = k; } }
    if (!key) return next();

    if (!(await isUserSubbed(ctx))) return ctx.reply("⚠️ Davom etish uchun kanallarga a'zo bo'ling!", getJoinKeyboard());

    if (key === 'global') {
        const btns = Object.keys(globalTestsDB).map(id => [Markup.button.callback(`🌍 ${globalTestsDB[id].title}`, `view|gl|${id}|15`)]);
        if (isAnyAdmin(ctx.from?.username)) btns.push([Markup.button.callback('➕ Yangi Test Yaratish', 'admin_create_gl')]);
        return ctx.reply(globalText, { parse_mode: 'Markdown', ...Markup.inlineKeyboard(btns) });
    }
    if (key === 'private') {
        const my = Object.keys(userTestsDB).filter(id => Number(userTestsDB[id].ownerId) === Number(ctx.from.id));
        const btns = my.map(id => [Markup.button.callback(`📁 ${userTestsDB[id].title}`, `view|my|${id}|15`)]);
        btns.push([Markup.button.callback('➕ Yangi Yaratish', 'create_my_test')]);
        return ctx.reply(myText, { parse_mode: 'Markdown', ...Markup.inlineKeyboard(btns) });
    }
    if (key === 'lang_btn') return ctx.reply("🌐 Tilni tanlang / Select Language:", Markup.inlineKeyboard([[Markup.button.callback('🇺🇿 Uzb', 'setlang|Uzbek'), Markup.button.callback('🇷🇺 Рус', 'setlang|Russian'), Markup.button.callback('🇬🇧 Eng', 'setlang|English')]]));
    if (key === 'prof') {
        const totalCreated = Object.keys(userTestsDB).filter(id => Number(userTestsDB[id].ownerId) === Number(ctx.from.id)).length;
        return ctx.reply(`👤 ID: ${ctx.from.id}\n🌐 Til: ${lang}\n📁 Yaratgan testlaringiz: ${totalCreated} ta`);
    }

    if (key === 'admin_btn' && isAnyAdmin(ctx.from?.username)) {
        return ctx.reply("🔑 **Admin Panel**\nTezkor va ixcham boshqaruv:", Markup.inlineKeyboard([
            [Markup.button.callback('➕ Test Yaratish', 'admin_create_gl')],
            [Markup.button.callback('➕ Admin Qo\'shish', 'sys_add_adm'), Markup.button.callback('❌ Admin O\'chirish', 'sys_del_adm')],
            [Markup.button.callback('📢 Majburiy Kanal Qo\'shish', 'sys_add_chan'), Markup.button.callback('🗑 Kanal O\'chirish', 'sys_rem_chan')],
            [Markup.button.callback('📣 Xabar: Barcha Foydalanuvchilarga', 'sys_bc_users')],
            [Markup.button.callback('📋 Adminlar Ro\'yxati', 'sys_list_adm')]
        ]));
    }
});

// ==========================================
// 7. ALL-IN-ONE COMPACT TEST VIEWER
// ==========================================
bot.action(/list\|(gl|my)/, (ctx) => {
    ctx.answerCbQuery().catch(() => { });
    const isGl = ctx.match[1] === 'gl';
    const db = isGl ? globalTestsDB : userTestsDB;
    const btns = Object.keys(db).filter(id => isGl || Number(db[id].ownerId) === Number(ctx.from.id)).map(id => [Markup.button.callback(`${isGl ? '🌍' : '📁'} ${db[id].title}`, `view|${ctx.match[1]}|${id}|15`)]);

    if (isGl && isAnyAdmin(ctx.from?.username)) btns.push([Markup.button.callback('➕ Yangi Test Yaratish', 'admin_create_gl')]);
    else if (!isGl) btns.push([Markup.button.callback('➕ Yangi Yaratish', 'create_my_test')]);

    return ctx.editMessageText(isGl ? globalText : myText, {
        parse_mode: 'Markdown',
        ...Markup.inlineKeyboard(btns)
    }).catch(()=>{});
});

bot.action(/view\|(gl|my)\|(.+)\|(\d+)/, (ctx) => {
    ctx.answerCbQuery().catch(() => { });
    const type = ctx.match[1]; const id = ctx.match[2]; const time = parseInt(ctx.match[3]);
    const test = type === 'gl' ? globalTestsDB[id] : userTestsDB[id];
    if (!test) return ctx.editMessageText("❌ Bu test o'chirilgan.");

    const nextTime = time === 15 ? 30 : time === 30 ? 60 : time === 60 ? 0 : 15;
    const timeLabel = time === 0 ? 'Cheksiz' : `${time} soniya`;

    const b = [
        [Markup.button.callback('▶️ YAKKA O\'YNASH', `play|${type}|${id}|${time}`), Markup.button.callback('🏟️ GURUHDA O\'YNASH', `host|${type}|${id}|${time}`)],
        [Markup.button.callback(`⏱ Vaqt: ${timeLabel} 🔄 (O'zgartirish)`, `view|${type}|${id}|${nextTime}`)],
        [Markup.button.callback('🔤 Tarjima qilish', `trans|${type}|${id}`)]
    ];

    if (type === 'my' || isAnyAdmin(ctx.from?.username)) {
        b.push([Markup.button.callback('➕ Savol (Poll) qo\'shish', `addpoll|${type}|${id}`), Markup.button.callback('🗑️ O\'chirish', `del|${type}|${id}`)]);
    }
    b.push([Markup.button.callback('🔙 Orqaga', `list|${type}`)]);

    return ctx.editMessageText(`📑 **Test:** ${test.title}\n❓ **Savollar soni:** ${test.questions.length}\n\nO'ynash uchun variantni tanlang:`, Markup.inlineKeyboard(b)).catch(() => { });
});

bot.action(/play\|(my|gl)\|(.+)\|(\d+)/, async (ctx) => {
    ctx.answerCbQuery().catch(() => { });
    const test = ctx.match[1] === 'gl' ? globalTestsDB[ctx.match[2]] : userTestsDB[ctx.match[2]];
    const time = parseInt(ctx.match[3]);
    
    if (!test) return ctx.editMessageText("❌ Bu test topilmadi.");

    const matchId = generateId();
    const uid = Number(ctx.from.id);
    const username = ctx.from.username ? `@${ctx.from.username}` : ctx.from.first_name;

    activeMatches[matchId] = {
        hostId: uid, 
        test: test, 
        players: new Set([uid]),
        scores: { [uid]: 0 }, 
        usernames: { [uid]: username }, 
        times: { [uid]: 0 },
        answered: { [uid]: 0 },
        timer: time, 
        status: 'lobby', 
        questionStart: 0, 
        isSolo: true
    };

    await ctx.deleteMessage().catch(() => { });
    await startQuiz(matchId, ctx);
});

bot.action(/host\|(my|gl)\|(.+)\|(\d+)/, (ctx) => {
    ctx.answerCbQuery().catch(() => { });
    const url = `https://t.me/${ctx.botInfo.username}?startgroup=match_${ctx.match[2]}_t${ctx.match[3]}`;
    return ctx.editMessageText(`🏟️ **Guruhga yuborish tayyor!**\n\nPastdagi tugmani bosib testingizni guruhga tashlang.`, Markup.inlineKeyboard([[Markup.button.url('➡️ Guruhni Tanlash', url)], [Markup.button.callback('🔙 Orqaga', `view|${ctx.match[1]}|${ctx.match[2]}|${ctx.match[3]}`)]]));
});

// ==========================================
// 8. MULTIPLAYER ARENA (GROUP LOGIC)
// ==========================================
bot.action(/join\|(.+)/, async (ctx) => {
    const matchId = ctx.match[1];
    const m = activeMatches[matchId];
    const uid = Number(ctx.from.id);

    if (!m || m.status !== 'lobby') return ctx.answerCbQuery("❌ Test allaqachon boshlangan yoki tugagan!", { show_alert: true });
    if (m.players.has(uid)) return ctx.answerCbQuery("✅ Siz allaqachon tayyorsiz!", { show_alert: true });

    m.players.add(uid);
    m.usernames[uid] = ctx.from.username ? `@${ctx.from.username}` : ctx.from.first_name;
    m.scores[uid] = 0;
    m.times[uid] = 0;
    m.answered[uid] = 0;

    ctx.answerCbQuery("✅ Tayyorsiz!");

    let list = Array.from(m.players).map(id => `• ${m.usernames[id]}`).join('\n');
    await ctx.editMessageText(`🎲 **${m.test.title}**\n\n🗡 Savollar: ${m.test.questions.length}\n⏱ Vaqt: ${m.timer > 0 ? m.timer + 's' : 'Cheksiz'}\n\n🤝 **Tayyor ishtirokchilar (${m.players.size}/2):**\n${list}`,
        Markup.inlineKeyboard([[Markup.button.callback('✋ Men tayyorman!', `join|${matchId}`)]])).catch(() => { });

    await autoStartIfReady(matchId, ctx);
});

// ==========================================
// MUKAMMAL JAVOBLARNI KUZATISH (ANTI-CHEAT)
// ==========================================
bot.on('poll_answer', (ctx) => {
    try {
        const answer = ctx.pollAnswer;
        const trk = pollTracker[answer.poll_id];
        if (!trk) return;
        
        const m = activeMatches[trk.matchId];
        if (!m || m.status !== 'playing') return;

        const uid = Number(answer.user.id);

        if (m.players.has(uid)) {
            // Takroriy bosishlarning oldini olish
            if (!trk.answeredUsers) trk.answeredUsers = new Set();
            if (trk.answeredUsers.has(uid)) return;
            trk.answeredUsers.add(uid);

            const rt = (Date.now() - m.questionStart) / 1000;
            
            m.answered = m.answered || {};
            m.answered[uid] = (m.answered[uid] || 0) + 1;
            m.times[uid] = (m.times[uid] || 0) + rt;

            const selectedOpt = Number(answer.option_ids[0]);
            const correctOpt = Number(trk.correctOpt);

            if (selectedOpt === correctOpt) {
                m.scores[uid] = (m.scores[uid] || 0) + 1;
            }
        }
    } catch (e) { console.error("Poll error:", e.message); }
});

// ==========================================
// 9. CREATION, ADMIN & SYSTEM CALLBACKS
// ==========================================
bot.action('admin_create_gl', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'name_gl'; return ctx.reply("📝 Umumiy test nomini kiriting:"); });
bot.action('create_my_test', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'name_my'; return ctx.reply("📝 Shaxsiy testingiz nomini kiriting:"); });
bot.action(/addpoll\|(my|gl)\|(.+)/, (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'addp'; ctx.session.target = ctx.match[2]; ctx.session.type = ctx.match[1]; return ctx.reply("📥 Menga tayyor Quiz (Viktorina) pollarni forward qiling yoki yarating.\n\nBarcha savollarni yuborib bo'lgach, pastdagi 'Tugatish' tugmasini bosing.", Markup.inlineKeyboard([[Markup.button.callback("✅ Tugatish", 'stop_poll')]])); });
bot.action(/trans\|(my|gl)\|(.+)/, (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'tr_lang'; ctx.session.target = ctx.match[2]; ctx.session.type = ctx.match[1]; return ctx.reply("🔤 Qaysi tilga tarjima qilamiz? (Masalan: ru, en, uz)"); });
bot.action('stop_poll', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = null; backupData(); return ctx.editMessageText("✅ Saqlandi va yakunlandi!").catch(() => { }); });
bot.action(/del\|(my|gl)\|(.+)/, (ctx) => { ctx.answerCbQuery().catch(() => { }); if (ctx.match[1] === 'gl') delete globalTestsDB[ctx.match[2]]; else delete userTestsDB[ctx.match[2]]; backupData(); return ctx.editMessageText("🗑️ Test muvaffaqiyatli o'chirildi."); });
bot.action(/setlang\|(.+)/, (ctx) => { ctx.answerCbQuery().catch(() => { }); userProfiles[ctx.from.id].lang = ctx.match[1]; backupData(); ctx.deleteMessage().catch(() => { }); return ctx.reply("✅ Til o'zgartirildi!", getMainMenu(ctx)); });

bot.action('sys_add_adm', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'sys_wait_username'; return ctx.reply("Yangi adminning username'ini yuboring (@ belgisiz):"); });
bot.action('sys_del_adm', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'sys_wait_del_username'; return ctx.reply("❌ O'chiriladigan adminning username'ini yuboring (@ belgisiz):"); });
bot.action('sys_list_adm', (ctx) => { ctx.answerCbQuery().catch(() => { }); return ctx.reply(`📋 **Adminlar:**\n${SUPER_ADMINS.map(a => `@${a} (Owner)`).join('\n')}\n${Array.from(adminsDB).map(a => `@${a}`).join('\n')}`); });
bot.action('sys_add_chan', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'sys_add_chan'; return ctx.reply("Majburiy kanal linki yoki @username ni yuboring:"); });
bot.action('sys_rem_chan', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'sys_rem_chan'; return ctx.reply(`Joriy kanallar:\n${Array.from(requiredChannels).join('\n')}\n\nO'chirish uchun kanalni yuboring:`); });
bot.action('sys_bc_users', (ctx) => { ctx.answerCbQuery().catch(() => { }); ctx.session.step = 'bc_users'; return ctx.reply("📢 Barcha foydalanuvchilarga yuboriladigan xabarni (rasm/video/matn) jo'nating:"); });

// ALL-PURPOSE MESSAGE CATCHER
bot.on('message', async (ctx, next) => {
    if (isGroup(ctx)) return next();
    const s = ctx.session;

    if (s.step === 'bc_users') {
        s.step = null;
        const statusMsg = await ctx.reply("⏳ Tarqatilmoqda...");
        let count = 0;
        for (const target of Object.keys(userProfiles)) {
            try {
                await ctx.telegram.copyMessage(target, ctx.chat.id, ctx.message.message_id);
                count++;
                await sleep(50);
            } catch (e) { }
        }
        return ctx.telegram.editMessageText(ctx.chat.id, statusMsg.message_id, undefined, `✅ Xabar ${count} kishiga yuborildi.`);
    }

    if (ctx.message.poll && s.step === 'addp') {
        const t = s.type === 'gl' ? globalTestsDB[s.target] : userTestsDB[s.target];
        if (!t) return;
        if (ctx.message.poll.type !== 'quiz') return ctx.reply("❌ Bu oddiy so'rovnoma! Menga Viktorina (Quiz) yuboring.");
        t.questions.push({ question: ctx.message.poll.question, options: ctx.message.poll.options, correct_option_id: ctx.message.poll.correct_option_id });
        return ctx.reply("✅ Qo'shildi! Yana yuboring yoki 'Tugatish' tugmasini bosing.", Markup.inlineKeyboard([[Markup.button.callback("✅ Tugatish", 'stop_poll')]]));
    }

    if (ctx.message.text) {
        const txt = ctx.message.text;

        if (s.step === 'sys_wait_username') {
            let cleanAdmin = txt.trim().replace('@', '').replace('https://t.me/', '');
            adminsDB.add(cleanAdmin); s.step = null; backupData();
            return ctx.reply(`✅ @${cleanAdmin} endi Admin!`);
        }

        if (s.step === 'sys_wait_del_username') {
            let cleanAdmin = txt.trim().replace('@', '').replace('https://t.me/', '');
            if (SUPER_ADMINS.some(a => a.toLowerCase() === cleanAdmin.toLowerCase())) return ctx.reply("❌ Super Adminni o'chira olmaysiz!");
            if (adminsDB.has(cleanAdmin)) {
                adminsDB.delete(cleanAdmin); s.step = null; backupData();
                return ctx.reply(`✅ @${cleanAdmin} adminlar qatoridan o'chirildi!`);
            }
            return ctx.reply("❌ Bunday admin topilmadi.");
        }

        if (s.step === 'sys_add_chan' || s.step === 'sys_rem_chan') {
            let chan = txt.trim();
            if (chan.includes('t.me/')) chan = '@' + chan.split('t.me/')[1];
            if (!chan.startsWith('@')) chan = '@' + chan;
            s.step === 'sys_add_chan' ? requiredChannels.add(chan) : requiredChannels.delete(chan);
            s.step = null; backupData();
            return ctx.reply(`✅ Kanal saqlandi/o'chirildi.`);
        }

        if (s.step === 'tr_lang') {
            s.step = null; const msg = await ctx.reply(`⏳ Tarjima qilinmoqda, kuting...`);
            const t = s.type === 'gl' ? globalTestsDB[s.target] : userTestsDB[s.target];
            const nid = generateId();
            try {
                const tt = await translateText(t.title, txt);
                const tq = [];
                for (let i = 0; i < t.questions.length; i++) {
                    const tqt = await translateText(t.questions[i].question, txt);
                    const to = [];
                    for (const o of t.questions[i].options) { to.push({ text: await translateText(o.text, txt) }); await sleep(400); }
                    tq.push({ question: tqt, options: to, correct_option_id: t.questions[i].correct_option_id });
                }
                userTestsDB[nid] = { id: nid, ownerId: ctx.from.id, title: `[${txt}] ${tt}`, questions: tq };
                backupData(); await ctx.telegram.editMessageText(ctx.chat.id, msg.message_id, undefined, `✅ Tarjima yakunlandi! Mening testlarim bo'limida ko'rishingiz mumkin.`);
            } catch (e) { ctx.reply("❌ Xatolik yuz berdi."); }
            return;
        }

        if (s.step === 'name_gl' || s.step === 'name_my') {
            const id = generateId();
            const isGl = s.step === 'name_gl';
            if (isGl) globalTestsDB[id] = { id, title: txt, questions: [] };
            else userTestsDB[id] = { id, ownerId: ctx.from.id, title: txt, questions: [] };

            s.step = 'addp';
            s.target = id;
            s.type = isGl ? 'gl' : 'my';
            backupData();
            return ctx.reply(`✅ **"${txt}"** yaratildi!\n\nEndi menga to'g'ridan-to'g'ri Quiz/Viktorina savollaringizni yuboring. Tugatgach pastdagi tugmani bosing:`, Markup.inlineKeyboard([[Markup.button.callback("✅ Tugatish", 'stop_poll')]]));
        }
    }
    return next();
});

// ==========================================
// 10. BOOT AND SERVER INIT
// ==========================================
async function startApp() {
    try {
        console.log("⏳ Connecting to MongoDB...");
        await mongoose.connect(MONGO_URI);
        const d = await DataStore.findOne({ id: 'main' });
        if (d) {
            Object.assign(globalTestsDB, d.globalTests || {});
            Object.assign(userTestsDB, d.userTests || {});
            Object.assign(userProfiles, d.profiles || {});
            (d.admins || []).forEach(a => adminsDB.add(a));
            if (d.channels) { requiredChannels.clear(); d.channels.forEach(c => requiredChannels.add(c)); }
        }

        console.log("🚀 Launching Telegram Bot...");
        // BARCHA EVENTLARNI ESHITISH (Eng muhim qism)
        await bot.launch({
            dropPendingUpdates: true,
            allowedUpdates: ['message', 'callback_query', 'poll', 'poll_answer', 'my_chat_member', 'chat_member']
        });
        
        bot.botInfo = await bot.telegram.getMe();
        console.log(`✅ UX-OPTIMIZED BOT ONLINE: @${bot.botInfo.username}`);
    } catch (e) { console.error("❌ CRITICAL ERROR:", e.message); }
}

const port = process.env.PORT || 3000;
http.createServer((req, res) => res.end('Bot is running alive with new UX')).listen(port, () => {
    console.log(`🌐 Server listening on port ${port}`);
    startApp();
});