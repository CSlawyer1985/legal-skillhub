# Known Issues & Gotchas

## 1. ⚠️ `ended=false` but video actually finished

**Symptom**: `ct === dur`, `paused=true`, but `ended=false`  
**Cause**: Some video players don't fire the `ended` event  
**Fix**: Always use `ct >= dur - 3` as the completion check, not just `ended === true`

## 2. ⚠️ Enrollment gate blocks video

**Symptom**: Navigated to course, no `<video>` element found  
**Cause**: Course from 课程广场 requires clicking "选修并学习" first  
**Fix**: After every navigate to a course detail page, check for `选修并学习` button before trying to play. Click it, wait 3s, handle the confirm dialog, wait 3s more, then play.

## 3. ⚠️ Angular Router — no href on course links

**Symptom**: `document.querySelectorAll('a[href*=courseId]')` returns empty  
**Cause**: Site uses Angular Router; links have no `href` attribute  
**Fix**: Use `history.pushState` intercept to capture the URL when clicking the card's `<a>` tag. Then `navigate` directly to that URL.

## 4. ⚠️ Aria refs expire on page reload

**Symptom**: `browser act click ref=eXXX` fails with timeout  
**Cause**: Refs are generated at snapshot time and expire when DOM changes  
**Fix**: Never use refs for clicking course cards. Always use JS `evaluate` with text matching.

## 5. ⚠️ Cron rate limit with short intervals

**Symptom**: `consecutiveErrors: 6`, error `API rate limit reached`  
**Cause**: Isolated agent cron jobs share model quota; firing every 2 minutes exhausts it  
**Fix**: Set `everyMs` to at least `480000` (8 minutes). For courses > 1 hour, `600000` (10 min) is safer.

## 6. ⚠️ Video paused by browser tab visibility

**Symptom**: Video was playing, then paused unexpectedly  
**Cause**: Browser may pause media when tab loses focus  
**Fix**: Cron monitoring loop checks for `paused=true` and calls `video.play()` to resume

## 7. ℹ️ `history.pushState` capture returns empty string

**Symptom**: JS intercept returns `''` or `'pending'`  
**Cause**: Angular router may use a different navigation method, or the click didn't fire  
**Fix**: Try `router.navigate` via Angular injector, or use `window.__ngZone__` injection. Fallback: use browser `snapshot` to find card links visually and click via `act`.
