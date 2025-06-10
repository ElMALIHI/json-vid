# Enhanced Video Composition API - Complete Endpoint Reference

## Authentication
All endpoints (except health checks) require API key authentication via Bearer token.

**Header Required:**
```
Authorization: Bearer your-secret-api-key
```

---

## 1. Basic Information Endpoints

### GET `/` - Root/Welcome
Get basic API information and features.

```bash
curl -X GET "http://localhost:8000/"
```

### GET `/health` - Health Check
Check API health status and current job statistics.

```bash
curl -X GET "http://localhost:8000/health"
```

### GET `/supported-formats` - Supported Formats
Get list of supported input/output formats and limits.

```bash
curl -X GET "http://localhost:8000/supported-formats"
```

### GET `/templates` - Composition Templates
Get predefined composition templates for common use cases.

```bash
curl -X GET "http://localhost:8000/templates"
```

### GET `/example-requests` - Example Requests
Get comprehensive example request structures.

```bash
curl -X GET "http://localhost:8000/example-requests"
```

---

## 2. File Upload Endpoints

### POST `/upload` - Upload Single File
Upload a single media file (image, audio, or video).

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer your-secret-api-key" \
  -F "file=@/path/to/your/image.jpg"
```

### POST `/upload-batch` - Upload Multiple Files
Upload multiple files at once.

```bash
curl -X POST "http://localhost:8000/upload-batch" \
  -H "Authorization: Bearer your-secret-api-key" \
  -F "files=@/path/to/image1.jpg" \
  -F "files=@/path/to/image2.png" \
  -F "files=@/path/to/audio.mp3"
```

---

## 3. Video Composition Endpoints

### POST `/compose` - Create Video Composition
Create a new video composition job with advanced features.

**Basic Slideshow Example:**
```bash
curl -X POST "http://localhost:8000/compose" \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": {
      "Scene 1": {
        "source": "https://example.com/image1.jpg",
        "duration": 3.0,
        "transition": "fade"
      },
      "Scene 2": {
        "source": "uploads/image2.jpg",
        "duration": 4.0,
        "transition": "slide_left",
        "voiceover": "uploads/narration.mp3"
      }
    },
    "quality": "high",
    "fps": 30
  }'
```

**Advanced Composition Example:**
```bash
curl -X POST "http://localhost:8000/compose" \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": {
      "Scene 1": {
        "source": "uploads/intro_video.mp4",
        "media_type": "video",
        "voiceover": "uploads/intro_narration.mp3",
        "background_music": "uploads/bg_music.mp3",
        "transition": "fade",
        "transition_duration": 1.0,
        "audio_settings": {
          "volume": 0.8,
          "effects": ["normalize"]
        },
        "video_settings": {
          "brightness": 1.1,
          "contrast": 1.05,
          "rotate": 0
        },
        "text_overlays": [
          {
            "text": "Welcome to Our Presentation",
            "position": "center",
            "font_size": 48,
            "font_color": "white",
            "background_color": "rgba(0,0,0,0.5)",
            "start_time": 1.0,
            "duration": 3.0
          }
        ]
      },
      "Scene 2": {
        "source": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
        "media_type": "image",
        "duration": 5.0,
        "transition": "zoom_in",
        "text_overlays": [
          {
            "text": "Chapter 2",
            "position": "top",
            "font_size": 36,
            "font_color": "yellow"
          }
        ]
      }
    },
    "quality": "ultra",
    "fps": 60,
    "priority": "high",
    "composition_settings": {
      "background_color": "black",
      "background_music": "uploads/global_bg.mp3",
      "background_music_volume": 0.3,
      "intro_duration": 2.0,
      "outro_duration": 3.0,
      "crossfade_audio": true
    },
    "webhook_url": "https://your-app.com/webhook/video-complete",
    "metadata": {
      "project_name": "Marketing Video",
      "client": "Acme Corp",
      "version": "1.0"
    }
  }'
```

---

## 4. Job Management Endpoints

### GET `/job/{job_id}` - Get Job Status
Get detailed status of a specific job.

```bash
curl -X GET "http://localhost:8000/job/12345678-1234-1234-1234-123456789abc"
```

### GET `/jobs` - List Jobs
List jobs with pagination and filtering.

**Basic listing:**
```bash
curl -X GET "http://localhost:8000/jobs"
```

**With pagination and filters:**
```bash
curl -X GET "http://localhost:8000/jobs?page=2&per_page=5&status=completed&priority=high"
```

### DELETE `/job/{job_id}` - Delete Job
Delete a job and its associated files.

```bash
curl -X DELETE "http://localhost:8000/job/12345678-1234-1234-1234-123456789abc" \
  -H "Authorization: Bearer your-secret-api-key"
```

### POST `/cancel/{job_id}` - Cancel Job
Cancel a processing or pending job.

```bash
curl -X POST "http://localhost:8000/cancel/12345678-1234-1234-1234-123456789abc" \
  -H "Authorization: Bearer your-secret-api-key"
```

---

## 5. Download Endpoints

### GET `/download/{job_id}` - Download Video
Download the generated video file.

```bash
curl -X GET "http://localhost:8000/download/12345678-1234-1234-1234-123456789abc" \
  -o "generated_video.mp4"
```

**Download with resume support:**
```bash
curl -X GET "http://localhost:8000/download/12345678-1234-1234-1234-123456789abc" \
  -o "generated_video.mp4" \
  -C -
```

---

## 6. Queue and Statistics Endpoints

### GET `/queue-status` - Queue Status
Get current processing queue status.

```bash
curl -X GET "http://localhost:8000/queue-status"
```

### GET `/statistics` - API Statistics
Get comprehensive API usage statistics.

```bash
curl -X GET "http://localhost:8000/statistics"
```

---

## 7. Testing and Development Endpoints

### POST `/test-webhook` - Test Webhook
Test webhook endpoint connectivity.

```bash
curl -X POST "http://localhost:8000/test-webhook" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://your-app.com/webhook/test"}'
```

---

## Complete Workflow Example

Here's a complete workflow from file upload to video download:

### Step 1: Upload files
```bash
# Upload images
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer your-secret-api-key" \
  -F "file=@image1.jpg"

curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer your-secret-api-key" \
  -F "file=@image2.jpg"

# Upload audio
curl -X POST "http://localhost:8000/upload" \
  -H "Authorization: Bearer your-secret-api-key" \
  -F "file=@narration.mp3"
```

### Step 2: Create composition
```bash
curl -X POST "http://localhost:8000/compose" \
  -H "Authorization: Bearer your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": {
      "Scene 1": {
        "source": "uploads/filename1.jpg",
        "duration": 4.0,
        "transition": "fade",
        "text_overlays": [
          {
            "text": "Welcome",
            "position": "center",
            "font_size": 48
          }
        ]
      },
      "Scene 2": {
        "source": "uploads/filename2.jpg",
        "duration": 4.0,
        "transition": "slide_left",
        "voiceover": "uploads/narration.mp3"
      }
    },
    "quality": "high",
    "webhook_url": "https://your-app.com/webhook"
  }'
```

### Step 3: Check job status
```bash
curl -X GET "http://localhost:8000/job/YOUR_JOB_ID"
```

### Step 4: Download completed video
```bash
curl -X GET "http://localhost:8000/download/YOUR_JOB_ID" \
  -o "final_video.mp4"
```

---

## Common Parameters and Values

### Video Quality Options:
- `"480p"` (low)
- `"720p"` (medium)
- `"1080p"` (high)
- `"1440p"` (ultra)
- `"2160p"` (uhd)

### Transition Types:
- `"fade"`, `"cut"`, `"slide_left"`, `"slide_right"`, `"slide_up"`, `"slide_down"`
- `"zoom_in"`, `"zoom_out"`, `"dissolve"`, `"crossfade"`
- `"wipe_left"`, `"wipe_right"`, `"circle_open"`, `"circle_close"`

### Job Priority:
- `"low"`, `"normal"`, `"high"`, `"urgent"`

### Job Status:
- `"pending"`, `"queued"`, `"processing"`, `"completed"`, `"failed"`, `"cancelled"`, `"expired"`

### Audio Effects:
- `"none"`, `"fade_in"`, `"fade_out"`, `"normalize"`, `"amplify"`, `"noise_reduction"`

### Text Positions:
- `"center"`, `"top"`, `"bottom"`, `"left"`, `"right"`

---

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found
- `413` - Payload Too Large (file size exceeded)
- `429` - Too Many Requests (queue full)
- `500` - Internal Server Error

Error responses include detailed error messages:
```json
{
  "detail": "Specific error message explaining what went wrong"
}
```