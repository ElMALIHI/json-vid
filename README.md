# Video Composition API

A FastAPI-based service for creating video compositions from images with voiceover support.

## API Endpoints

### Root Endpoint

Get API information:

```bash
curl http://localhost:8000/
```

### Upload Audio Files

#### Single Audio Upload

Upload a single audio file:

```bash
curl -X POST http://localhost:8000/upload-audio \
  -F "file=@/path/to/audio.mp3"
```

#### Multiple Audio Upload

Upload multiple audio files:

```bash
curl -X POST http://localhost:8000/upload-multiple-audio \
  -F "files=@/path/to/audio1.mp3" \
  -F "files=@/path/to/audio2.mp3"
```

### Video Composition

#### Create Video Composition

Create a new video composition job:

```bash
curl -X POST http://localhost:8000/compose \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": {
      "Scene 1": {
        "source": "https://example.com/image1.jpg",
        "voiceover": "uploads/audio_file_123.mp3",
        "transition": "fade",
        "duration": 5.0
      }
    },
    "output_format": "mp4",
    "resolution": "1920x1080",
    "fps": 30
}'
```

### Job Management

#### Get Job Status

Get the status of a specific job:

```bash
curl http://localhost:8000/job/{job_id}
```

#### List All Jobs

Get a list of all video composition jobs:

```bash
curl http://localhost:8000/jobs
```

#### Delete Job

Delete a specific job:

```bash
curl -X DELETE http://localhost:8000/job/{job_id}
```

### Example Request

Get example request formats:

```bash
curl http://localhost:8000/example
```

## Request Format Options

### 1. Using URLs for Source and Voiceover

```json
{
  "scenes": {
    "Scene 1": {
      "source": "https://example.com/image1.jpg",
      "voiceover": "https://example.com/audio1.mp3",
      "transition": "fade"
    }
  }
}
```

### 2. Using File Paths for Voiceover

```json
{
  "scenes": {
    "Scene 1": {
      "source": "https://example.com/image1.jpg",
      "voiceover": "uploads/audio_file_123.mp3",
      "transition": "fade"
    }
  }
}
```

### 3. Using Base64 Encoded Audio

```json
{
  "scenes": {
    "Scene 1": {
      "source": "https://example.com/image1.jpg",
      "voiceover_base64": "base64_encoded_audio_data",
      "transition": "fade"
    }
  }
}
```

## Available Transition Types

- `fade`
- `cut`
- `slide_left`
- `slide_right`
- `slide_up`
- `slide_down`
- `zoom_in`
- `zoom_out`
- `dissolve`

## Job Status Types

- `pending`: Job has been created but not yet started
- `processing`: Job is currently being processed
- `completed`: Job has finished successfully
- `failed`: Job failed with an error

## Workflow Steps

1. Upload your audio files using `POST /upload-audio`
2. Use the returned file path in your scenes configuration
3. Send the composition request
4. Monitor job status using the job ID
5. Once completed, access the generated video through the provided output URL
