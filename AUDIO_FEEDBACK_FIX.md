# Audio Feedback Fix - Self-Interruption Issue

## Problem

The system was picking up its own voice when ADA was speaking, causing:
- Self-interruption (AI interrupting itself)
- Laggy/stuttering speech
- Feedback loop where AI's voice → mic → Gemini → AI's voice (repeated)

## Root Cause

**Location:** `backend/ada.py` - `listen_audio()` method (line ~432)

The microphone audio was **always** being sent to Gemini, even when the AI was speaking:

```python
# OLD CODE (BROKEN):
data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)

# 1. Send Audio - ALWAYS SENT, even when AI is speaking!
if self.out_queue:
    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

# 2. VAD Logic - checks if AI is speaking, but audio already sent above
if ai_speaking:
    continue  # Only skips video frame, audio was already sent!
```

**The Problem:**
1. Mic captures audio (including AI's voice from speakers)
2. Audio sent to Gemini immediately (line 432)
3. VAD check happens later (line 445+) but audio already sent
4. Gemini processes AI's own voice → causes confusion/interruption

## Solution

**Fixed in:** `backend/ada.py` lines 432-472

**Key Changes:**

1. **Check AI speaking status BEFORE sending audio:**
   ```python
   # Check if AI is speaking FIRST
   ai_speaking = self._ai_is_speaking
   
   # Only send audio if AI is NOT speaking
   if not ai_speaking and not in_cooldown:
       await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
   else:
       # Skip sending audio - prevents feedback loop
       continue
   ```

2. **Added cooldown period:**
   - After AI stops speaking, wait 0.3 seconds before resuming mic input
   - Prevents picking up the tail end of AI speech
   - Configurable via `AI_SPEECH_COOLDOWN` constant

3. **Improved AI speech detection:**
   - Checks both `_ai_is_speaking` flag AND audio queue size
   - More reliable detection of when AI is actually speaking

## How It Works Now

```
1. Read audio from microphone
   ↓
2. Check: Is AI currently speaking?
   ├─ YES → Skip sending audio (prevents feedback)
   └─ NO → Continue
   ↓
3. Check: Are we in cooldown period?
   ├─ YES → Skip sending audio (prevents tail-end pickup)
   └─ NO → Send audio to Gemini
   ↓
4. Process VAD for video frames (if needed)
```

## Testing

After the fix, you should experience:
- ✅ No self-interruption when AI is speaking
- ✅ Smooth, uninterrupted AI speech
- ✅ Clean user input detection
- ✅ No feedback loops

## Debug Logs

Watch for these log messages to verify the fix is working:

```
[ADA DEBUG] [VAD] AI started speaking (audio data received)
[ADA DEBUG] [VAD] AI speech timeout reached. Starting cooldown period.
[ADA DEBUG] [VAD] Cooldown period ended. Resuming full mic input.
```

If you see audio being sent while AI is speaking, the fix may need adjustment.

## Configuration

You can adjust the cooldown period in `ada.py`:

```python
AI_SPEECH_COOLDOWN = 0.3  # Seconds (default: 0.3)
```

- **Lower value (0.1-0.2)**: Faster response, may pick up tail end
- **Higher value (0.4-0.5)**: More conservative, slight delay before accepting input

## Additional Notes

- The fix maintains all existing functionality
- Interruption feature still works (user can interrupt AI)
- Video frame sending logic unchanged
- No changes needed to frontend or other components

## If Issues Persist

1. **Check audio device settings:**
   - Ensure speakers and mic are properly configured
   - Try reducing speaker volume
   - Use headphones to eliminate acoustic feedback

2. **Adjust VAD threshold:**
   ```python
   VAD_THRESHOLD = 800  # Increase if too sensitive
   ```

3. **Check AI speech detection:**
   - Verify `_ai_is_speaking` flag is being set correctly
   - Check audio queue size detection

4. **Enable debug logging:**
   - Look for `[ADA DEBUG] [VAD]` messages
   - Verify cooldown periods are working

