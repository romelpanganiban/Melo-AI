# Ollama Setup Guide for Melo-AI

## Step 1: Install Ollama

### Windows
1. Download Ollama from [ollama.ai](https://ollama.ai)
2. Run the installer
3. Ollama will start automatically

### macOS
1. Download from [ollama.ai](https://ollama.ai)
2. Run the installer
3. Ollama will be available in your terminal

### Linux
```bash
curl https://ollama.ai/install.sh | sh
ollama serve
```

---

## Step 2: Verify Ollama is Running

Open a terminal/command prompt and run:
```bash
curl http://localhost:11434/api/tags
```

If successful, you should see:
```json
{"models": []}
```

---

## Step 3: Download Qwen3-8B Model

### Option 1: Download Qwen3-8B (Recommended for most users)
```bash
ollama pull qwen3:8b
```

This will download the 8B parameter model (~5GB).

### Option 2: Download Larger Models
- **Qwen3-32B**: Better quality but slower
  ```bash
  ollama pull qwen3:32b
  ```

- **Qwen2.5-Coder**: Great for coding assistance
  ```bash
  ollama pull qwen2.5-coder:7b
  ```

### Check Downloaded Models
```bash
ollama list
```

---

## Step 4: Configure Melo-AI

### Create `.env` file in `backend/` directory

Copy the contents from `backend/.env.example`:

```bash
# API Configuration
API_HOST=127.0.0.1
API_PORT=8000

# ... other config ...

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_TIMEOUT=300
OLLAMA_TEMPERATURE=0.7
```

**Important Settings:**
- `OLLAMA_BASE_URL`: URL where Ollama server is running (default: localhost:11434)
- `OLLAMA_MODEL`: Model name to use (default: qwen3:8b)
- `OLLAMA_TEMPERATURE`: Creativity level (0.0=deterministic, 2.0=very creative)
  - Recommended: 0.7 (balanced)
- `OLLAMA_TIMEOUT`: Max seconds to wait for response (default: 300)

---

## Step 5: Start Services

### Terminal 1: Start Ollama Server
```bash
ollama serve
```

The server will run on `http://localhost:11434`

### Terminal 2: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Terminal 3: Start Backend
```bash
cd backend
python -m uvicorn main:app --reload
```

Backend will run on `http://127.0.0.1:8000`

### Terminal 4: Start Frontend
```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:3000`

---

## Step 6: Test the Integration

1. Open browser to `http://localhost:3000/chat`
2. Click "+ New Chat"
3. Type a message and press Enter
4. You should see the AI response from Ollama!

---

## Troubleshooting

### Issue: "Cannot connect to Ollama at http://localhost:11434"
**Solution:**
- Make sure Ollama server is running (`ollama serve` in terminal)
- Check OLLAMA_BASE_URL in your `.env` file
- Verify Ollama is listening on port 11434

### Issue: "Model not available: qwen3:8b"
**Solution:**
- Download the model: `ollama pull qwen3:8b`
- Check available models: `ollama list`
- Verify model name in `.env` matches exactly

### Issue: Requests timeout after 300 seconds
**Solution:**
- Increase `OLLAMA_TIMEOUT` in `.env`
- Check system resources (CPU, RAM)
- Try a smaller model (qwen3:8b instead of 32b)

### Issue: Backend running but responses are slow
**Solution:**
- This is normal for the first request (model loading)
- Subsequent requests will be faster
- Consider reducing `OLLAMA_TEMPERATURE` to 0.5 for faster responses
- Monitor system resources during responses

---

## Model Information

### Qwen3-8B
- **Size**: ~5GB
- **Speed**: Fast
- **Quality**: Good
- **RAM Required**: 8GB+
- **Best For**: General chat, balanced performance

### Qwen3-32B
- **Size**: ~20GB
- **Speed**: Slower
- **Quality**: Excellent
- **RAM Required**: 32GB+
- **Best For**: Complex reasoning, coding

### Qwen2.5-Coder
- **Size**: ~4GB
- **Speed**: Fast
- **Quality**: Excellent for code
- **RAM Required**: 8GB+
- **Best For**: Coding assistance, file analysis

---

## Next Steps

- [x] Install Ollama
- [x] Download Qwen3-8B
- [x] Configure Melo-AI
- [x] Start services
- [ ] Test the chat
- [ ] Customize system prompt in `.env`
- [ ] Fine-tune temperature/model based on your needs

---

## Documentation Links

- [Ollama Official Docs](https://github.com/ollama/ollama)
- [Qwen3 Model Card](https://huggingface.co/Qwen)
- [Ollama API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)
