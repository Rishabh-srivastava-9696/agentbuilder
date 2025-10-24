# 🧪 Quick Test Guide - Streaming Response

## ⚡ Quick Test (5 minutes)

### 1. Start the Widget (if not running)
```bash
cd apps/widget
npm run dev
```

### 2. Open in Browser
```
http://localhost:5173/?agent_id=f168131d-7833-4f9c-ac8e-8a19b22c16f3
```

### 3. Send Test Message
Type in the chat:
```
Show me faucets under 5000 rupees
```

### 4. What You Should See ✨

**Before (if streaming works):**
- Message appears immediately in chat
- Empty assistant message appears
- **Text starts flowing in word-by-word**
- Response builds up progressively
- Citations appear at the end

**What to Watch For:**
- ✅ Response appears within 1 second (first token)
- ✅ Text flows smoothly, word-by-word
- ✅ No flickering or glitches
- ✅ Citations appear after text completes
- ✅ No errors in console

---

## 🔍 Detailed Testing

### Test Messages

1. **Short Query**
   ```
   Hello
   ```
   Expected: Quick streaming response

2. **Medium Query** 
   ```
   What products do you have?
   ```
   Expected: Moderate streaming response

3. **Long Query with RAG**
   ```
   Tell me about all your bathroom products including faucets, showers, and toilets with detailed specifications
   ```
   Expected: Long streaming response with citations

4. **Product Search**
   ```
   Show me faucets under 5000 rupees
   ```
   Expected: Streamed response with product citations

---

## 🎯 What to Verify

### Visual Behavior

- [ ] Text appears progressively (not all at once)
- [ ] Smooth word-by-word flow
- [ ] No "jumps" or repositioning
- [ ] Message container grows smoothly
- [ ] Citations appear at the end
- [ ] Scrolling works during streaming

### Timing

- [ ] First token appears in <1 second
- [ ] Steady stream of tokens (not bursts)
- [ ] Complete response arrives
- [ ] No hanging/frozen streams

### Console (F12)

Open browser console and check:

- [ ] No red errors
- [ ] Status messages logged:
  ```
  Status: Processing message...
  Status: Retrieving context...
  Status: Loading memory...
  ```
- [ ] Streaming chunks visible

### Network Tab (F12)

1. Open DevTools → Network tab
2. Send a message
3. Look for `POST /api/v1/messages/stream`
4. Click on the request
5. Check "Response" tab

You should see:
```
data: {"type":"status","content":"Processing message..."}

data: {"type":"content","content":"Based"}

data: {"type":"content","content":" on"}

data: {"type":"content","content":" your"}
```

---

## 🐛 Troubleshooting

### Problem: Response appears all at once (not streaming)

**Check:**
- Is the `/stream` endpoint being called? (Network tab)
- Any errors in console?
- Is backend running? (`http://localhost:8000/health`)

**Try:**
- Refresh the page
- Check API is running: `curl http://localhost:8000/health`
- Check browser console for errors

### Problem: No response at all

**Check:**
- Backend running? (`cd apps/api && ./start.sh`)
- Correct agent_id in URL?
- Network errors in console?

**Try:**
- Check API logs: `tail -f apps/api/logs/api.log`
- Test regular endpoint: Send message without streaming
- Verify agent exists in database

### Problem: Stream cuts off early

**Check:**
- Backend logs for errors
- Network tab - did request complete?
- Console errors?

**Try:**
- Send a shorter message
- Check backend health
- Restart backend if needed

### Problem: Multiple messages appear

**Check:**
- Is placeholder message created correctly?
- Same message ID used for updates?

**Fix:**
- Check App.tsx - verify message ID consistency

---

## 📊 Expected Performance

| Metric | Target | How to Measure |
|--------|--------|----------------|
| **Time to First Token** | <1 second | Start timing when send clicked |
| **Streaming Speed** | Smooth, readable | Visual observation |
| **Total Response Time** | Similar to before | End-to-end timing |
| **No Errors** | 0 console errors | Browser console |

---

## ✅ Success Checklist

After testing, verify:

- [ ] ✅ Streaming works visually
- [ ] ✅ First token appears quickly (<1s)
- [ ] ✅ Text flows smoothly word-by-word
- [ ] ✅ No console errors
- [ ] ✅ Citations appear after text
- [ ] ✅ Multiple messages work (send 3-4 in a row)
- [ ] ✅ Short and long messages both work
- [ ] ✅ Works in different browser tabs
- [ ] ✅ Page refresh maintains functionality

---

## 🎬 Demo Flow

**Perfect Demo:**

1. Open widget: http://localhost:5173/?agent_id=f168131d-7833-4f9c-ac8e-8a19b22c16f3
2. Send: "Show me faucets under 5000 rupees"
3. **Watch response stream in** ✨
4. Citations appear at end
5. Send: "Tell me more about the first one"
6. **Watch follow-up stream in** ✨
7. Check console - no errors

**What makes it successful:**
- Response starts appearing almost immediately
- Text flows naturally, word-by-word
- Feels like a real conversation
- No waiting for complete response

---

## 📸 What Success Looks Like

### Before Streaming (Old Behavior)
```
User: Show me faucets
[3 seconds of loading spinner]
Assistant: [Complete response appears at once]
```

### After Streaming (New Behavior) ✨
```
User: Show me faucets
[<1 second]
Assistant: Based on
Assistant: Based on your
Assistant: Based on your budget,
Assistant: Based on your budget, here
Assistant: Based on your budget, here are
... (text flows in smoothly)
```

---

## 🚀 Next Steps After Testing

Once streaming is verified working:

1. **Add Visual Indicators**
   - Typing indicator while waiting for first token
   - Cursor/blinking at end of streaming message
   - Status messages in UI (optional)

2. **Error Handling**
   - Network interruption handling
   - Timeout handling (no response for X seconds)
   - Retry logic

3. **Performance Optimization**
   - Throttle updateMessage calls (batch every 50ms)
   - Avoid re-rendering entire message list

4. **Move to Next Roadmap Item**
   - BM25 Threshold Optimization
   - Enhanced Citations UI

---

**Ready to Test!** 🎉

Open http://localhost:5173/?agent_id=f168131d-7833-4f9c-ac8e-8a19b22c16f3 and send a message to see streaming in action!
