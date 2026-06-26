require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { v4: uuidv4 } = require('uuid');
const OpenAI = require('openai');

const app = express();
app.use(cors());
app.use(express.json());
app.use(express.static('.'));

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY || 'demo-key' });

// In-memory store (replace with DB in production)
const users = new Map();
const automations = new Map();
const logs = [];

// === AI AUTOMATION ENGINE ===

class AutomationEngine {
  constructor() {
    this.rules = new Map();
  }

  async processEmail(email) {
    const prompt = `Проанализируй письмо и верни JSON:
    {
      "priority": "high|medium|low",
      "category": "support|sales|billing|other",
      "summary": "краткое содержание",
      "suggestedReply": "предложенный ответ",
      "action": "reply|forward|escalate|ignore"
    }
    
    Письмо:
    От: ${email.from}
    Тема: ${email.subject}
    Текст: ${email.body}`;

    return this.callAI(prompt);
  }

  async processDocument(text) {
    const prompt = `Извлеки данные из документа и верни JSON:
    {
      "type": "invoice|contract|report|other",
      "data": { "ключевые поля": "значения" },
      "summary": "краткое описание",
      "amount": "сумма если есть"
    }
    
    Документ:
    ${text}`;

    return this.callAI(prompt);
  }

  async generateReport(data) {
    const prompt = `Составь бизнес-отчёт на основе данных:
    ${JSON.stringify(data, null, 2)}
    
    Формат: краткий, с выводами и рекомендациями.`;

    return this.callAI(prompt);
  }

  async chatReply(message, context) {
    const prompt = `Ты AI-ассистент для поддержки клиентов.
    Контекст: ${context || 'Общая консультация'}
    
    Сообщение клиента: ${message}
    
    Отвечай вежливо, по делу, на русском языке. Если вопрос сложный — предложи связаться с оператором.`;

    return this.callAI(prompt);
  }

  async callAI(prompt) {
    try {
      const completion = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.3,
      });
      return { success: true, result: completion.choices[0].message.content };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

const engine = new AutomationEngine();

// === API ROUTES ===

// Auth
app.post('/api/auth/register', (req, res) => {
  const { name, email, company } = req.body;
  const id = uuidv4();
  const user = { id, name, email, company, plan: 'trial', credits: 100, createdAt: new Date() };
  users.set(id, user);
  res.json({ success: true, user, token: id });
});

app.post('/api/auth/login', (req, res) => {
  const { email } = req.body;
  for (const [id, user] of users) {
    if (user.email === email) {
      return res.json({ success: true, user, token: id });
    }
  }
  res.status(404).json({ error: 'Пользователь не найден' });
});

// Automations
app.post('/api/automations', (req, res) => {
  const { type, name, config } = req.body;
  const id = uuidv4();
  const automation = { id, type, name, config, status: 'active', createdAt: new Date() };
  automations.set(id, automation);
  res.json({ success: true, automation });
});

app.get('/api/automations', (req, res) => {
  const list = Array.from(automations.values());
  res.json({ automations: list });
});

// AI Processing
app.post('/api/process/email', async (req, res) => {
  const { from, subject, body } = req.body;
  const result = await engine.processEmail({ from, subject, body });
  logs.push({ type: 'email', input: req.body, result, timestamp: new Date() });
  res.json(result);
});

app.post('/api/process/document', async (req, res) => {
  const { text } = req.body;
  const result = await engine.processDocument(text);
  logs.push({ type: 'document', input: req.body, result, timestamp: new Date() });
  res.json(result);
});

app.post('/api/process/report', async (req, res) => {
  const { data } = req.body;
  const result = await engine.generateReport(data);
  logs.push({ type: 'report', input: req.body, result, timestamp: new Date() });
  res.json(result);
});

app.post('/api/chat', async (req, res) => {
  const { message, context } = req.body;
  const result = await engine.chatReply(message, context);
  logs.push({ type: 'chat', input: req.body, result, timestamp: new Date() });
  res.json(result);
});

// Analytics
app.get('/api/analytics', (req, res) => {
  const totalProcessed = logs.length;
  const byType = {};
  logs.forEach(l => { byType[l.type] = (byType[l.type] || 0) + 1; });
  res.json({ totalProcessed, byType, activeAutomations: automations.size });
});

// Health
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', uptime: process.uptime(), version: '1.0.0' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`AI-Automator running on http://localhost:${PORT}`);
});
