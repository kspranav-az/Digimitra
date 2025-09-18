"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Slider } from "@/components/ui/slider"
import {
  Camera,
  Grid3X3,
  Maximize2,
  Play,
  Volume2,
  VolumeX,
  Zap,
  Search,
  Pin,
  X,
  Clock,
  Pause,
  SkipBack,
  SkipForward,
} from "lucide-react"

interface CameraFeed {
  id: string
  name: string
  location: string
  status: "online" | "offline" | "alert"
  lastActivity: string
  aiSuggestion?: string
  priority: number
  isRecording: boolean
  hasAudio: boolean
  resolution: string
}

interface AINotification {
  id: string
  cameraId: string
  message: string
  timestamp: string
  type: "motion" | "alert" | "suggestion"
  action?: string
}

export function LiveFeedWall() {
  const [gridSize, setGridSize] = useState<"2x2" | "3x3" | "4x4">("3x3")
  const [selectedFeeds, setSelectedFeeds] = useState<string[]>([])
  const [fullscreenFeed, setFullscreenFeed] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [autoArrange, setAutoArrange] = useState(true)
  const [showAISuggestions, setShowAISuggestions] = useState(true)
  const [isPlaying, setIsPlaying] = useState(true)
  const [currentTime, setCurrentTime] = useState("14:32:15")
  const [isLive, setIsLive] = useState(true)
  const [volume, setVolume] = useState(75)
  const [isMuted, setIsMuted] = useState(false)
  const [progress, setProgress] = useState(45) // Progress percentage for playback
  const [duration, setDuration] = useState("01:23:45") // Total duration

  // Mock camera feeds data
  const allFeeds: CameraFeed[] = [
    {
      id: "1",
      name: "Camera 01",
      location: "Main Entrance",
      status: "online",
      lastActivity: "Live",
      aiSuggestion: "High traffic area - recommended for monitoring",
      priority: 9,
      isRecording: true,
      hasAudio: true,
      resolution: "1080p",
    },
    {
      id: "2",
      name: "Camera 02",
      location: "Parking Lot A",
      status: "alert",
      lastActivity: "Motion detected 30s ago",
      aiSuggestion: "⚠️ Suspicious motion detected at 02:14",
      priority: 10,
      isRecording: true,
      hasAudio: false,
      resolution: "720p",
    },
    {
      id: "3",
      name: "Camera 03",
      location: "Emergency Exit",
      status: "online",
      lastActivity: "Live",
      aiSuggestion: "Person loitering detected - want to zoom in?",
      priority: 7,
      isRecording: true,
      hasAudio: true,
      resolution: "1080p",
    },
    {
      id: "4",
      name: "Camera 04",
      location: "Loading Dock",
      status: "offline",
      lastActivity: "1 hour ago",
      priority: 3,
      isRecording: false,
      hasAudio: false,
      resolution: "720p",
    },
    {
      id: "5",
      name: "Camera 05",
      location: "Reception Area",
      status: "online",
      lastActivity: "Live",
      aiSuggestion: "Person loitering detected - want to zoom in?",
      priority: 8,
      isRecording: true,
      hasAudio: true,
      resolution: "4K",
    },
    {
      id: "6",
      name: "Camera 06",
      location: "Corridor B",
      status: "alert",
      lastActivity: "Alert 2m ago",
      aiSuggestion: "⚠️ Unusual activity - auto-switched to priority view",
      priority: 9,
      isRecording: true,
      hasAudio: false,
      resolution: "1080p",
    },
    {
      id: "7",
      name: "Camera 07",
      location: "Cafeteria",
      status: "online",
      lastActivity: "Live",
      priority: 5,
      isRecording: true,
      hasAudio: true,
      resolution: "720p",
    },
    {
      id: "8",
      name: "Camera 08",
      location: "Server Room",
      status: "online",
      lastActivity: "Live",
      priority: 6,
      isRecording: true,
      hasAudio: false,
      resolution: "1080p",
    },
    {
      id: "9",
      name: "Camera 09",
      location: "Rooftop",
      status: "online",
      lastActivity: "Live",
      aiSuggestion: "High traffic area - recommended for monitoring",
      priority: 4,
      isRecording: true,
      hasAudio: false,
      resolution: "4K",
    },
  ]

  // Mock AI notifications
  const aiNotifications: AINotification[] = [
    {
      id: "1",
      cameraId: "2",
      message: "Suspicious motion detected at Camera 02. Want to zoom in?",
      timestamp: "30s ago",
      type: "alert",
      action: "zoom",
    },
    {
      id: "2",
      cameraId: "5",
      message: "Person loitering near Reception Area for 8+ minutes",
      timestamp: "2m ago",
      type: "suggestion",
      action: "focus",
    },
    {
      id: "3",
      cameraId: "6",
      message: "Auto-switched Camera 06 to priority view due to unusual activity",
      timestamp: "3m ago",
      type: "motion",
    },
  ]

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying)
    if (isLive && !isPlaying) {
      setIsLive(false) // When pausing live feed, switch to playback mode
    }
  }

  const handleGoLive = () => {
    setIsLive(true)
    setIsPlaying(true)
    setCurrentTime("14:32:15")
    setProgress(100) // Live is at 100% progress
  }

  const handleSkipBack = () => {
    if (isLive) return // Can't skip back in live mode
    const [hours, minutes, seconds] = currentTime.split(":").map(Number)
    const totalSeconds = Math.max(0, hours * 3600 + minutes * 60 + seconds - 10)
    const newHours = Math.floor(totalSeconds / 3600)
    const newMinutes = Math.floor((totalSeconds % 3600) / 60)
    const newSecs = totalSeconds % 60
    setCurrentTime(
      `${newHours.toString().padStart(2, "0")}:${newMinutes.toString().padStart(2, "0")}:${newSecs.toString().padStart(2, "0")}`,
    )
    setProgress(Math.max(0, progress - 5))
  }

  const handleSkipForward = () => {
    if (isLive) return // Can't skip forward in live mode
    const [hours, minutes, seconds] = currentTime.split(":").map(Number)
    const totalSeconds = hours * 3600 + minutes * 60 + seconds + 10
    const newHours = Math.floor(totalSeconds / 3600)
    const newMinutes = Math.floor((totalSeconds % 3600) / 60)
    const newSecs = totalSeconds % 60
    setCurrentTime(
      `${newHours.toString().padStart(2, "0")}:${newMinutes.toString().padStart(2, "0")}:${newSecs.toString().padStart(2, "0")}`,
    )
    setProgress(Math.min(100, progress + 5))
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
  }

  const handleViewCamera = (cameraId: string) => {
    setFullscreenFeed(cameraId)
    setIsLive(true)
    setIsPlaying(true)
  }

  const handlePlayback = (cameraId: string) => {
    setFullscreenFeed(cameraId)
    setIsLive(false)
    setIsPlaying(false)
    setCurrentTime("12:00:00") // Start from a specific time for playback
    setProgress(0) // Start from beginning
  }

  const handleProgressChange = (value: number[]) => {
    if (isLive) return // Can't change progress in live mode
    setProgress(value[0])
    // Calculate time based on progress
    const totalDurationSeconds = 5025 // 01:23:45 in seconds
    const currentSeconds = Math.floor((value[0] / 100) * totalDurationSeconds)
    const hours = Math.floor(currentSeconds / 3600)
    const minutes = Math.floor((currentSeconds % 3600) / 60)
    const seconds = currentSeconds % 60
    setCurrentTime(
      `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`,
    )
  }

  const getGridDimensions = () => {
    switch (gridSize) {
      case "2x2":
        return { cols: 2, rows: 2, maxFeeds: 4 }
      case "3x3":
        return { cols: 3, rows: 3, maxFeeds: 9 }
      case "4x4":
        return { cols: 4, rows: 4, maxFeeds: 16 }
      default:
        return { cols: 3, rows: 3, maxFeeds: 9 }
    }
  }

  const { cols, maxFeeds } = getGridDimensions()

  // Auto-arrange feeds based on AI priority
  const getDisplayFeeds = () => {
    let feeds = allFeeds.filter(
      (feed) =>
        feed.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        feed.location.toLowerCase().includes(searchQuery.toLowerCase()),
    )

    if (selectedFeeds.length > 0) {
      feeds = feeds.filter((feed) => selectedFeeds.includes(feed.id))
    }

    if (autoArrange) {
      feeds = feeds.sort((a, b) => b.priority - a.priority)
    }

    return feeds.slice(0, maxFeeds)
  }

  const displayFeeds = getDisplayFeeds()

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "bg-green-500"
      case "alert":
        return "bg-red-500 animate-pulse"
      case "offline":
        return "bg-gray-500"
      default:
        return "bg-gray-500"
    }
  }

  const toggleFeedSelection = (feedId: string) => {
    setSelectedFeeds((prev) => (prev.includes(feedId) ? prev.filter((id) => id !== feedId) : [...prev, feedId]))
  }

  const handleAIAction = (notification: AINotification) => {
    if (notification.action === "zoom" || notification.action === "focus") {
      setFullscreenFeed(notification.cameraId)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Live Feed Wall</h1>
          <p className="text-muted-foreground">Smart grid layout with AI-powered suggestions</p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant={autoArrange ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoArrange(!autoArrange)}
            className={!autoArrange ? "bg-transparent" : ""}
          >
            <Zap className="w-4 h-4 mr-2" />
            AI Auto-Arrange
          </Button>
        </div>
      </div>

      {/* AI Notifications */}
      {showAISuggestions && aiNotifications.length > 0 && (
        <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-purple-500/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-purple-400" />
                AI Suggestions
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={() => setShowAISuggestions(false)}>
                <X className="w-4 h-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {aiNotifications.slice(0, 2).map((notification) => (
                <div
                  key={notification.id}
                  className="flex items-center justify-between p-3 bg-purple-500/10 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
                    <div>
                      <p className="text-sm text-foreground">{notification.message}</p>
                      <p className="text-xs text-muted-foreground">{notification.timestamp}</p>
                    </div>
                  </div>
                  {notification.action && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAIAction(notification)}
                      className="bg-transparent border-purple-500/30 hover:bg-purple-500/10"
                    >
                      {notification.action === "zoom" ? "Zoom In" : "Focus"}
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search cameras..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64"
            />
          </div>
          <Select value={gridSize} onValueChange={(value: any) => setGridSize(value)}>
            <SelectTrigger className="w-24">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2x2">2×2</SelectItem>
              <SelectItem value="3x3">3×3</SelectItem>
              <SelectItem value="4x4">4×4</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">{displayFeeds.length} feeds</Badge>
          <Button variant="outline" size="sm" className="bg-transparent">
            <Grid3X3 className="w-4 h-4 mr-2" />
            Layout
          </Button>
        </div>
      </div>

      {/* Feed Grid */}
      <div
        className={`grid gap-4`}
        style={{
          gridTemplateColumns: `repeat(${cols}, 1fr)`,
        }}
      >
        {displayFeeds.map((feed) => (
          <Card
            key={feed.id}
            className={`bg-card/50 backdrop-blur-sm border-slate-700/50 hover:bg-card/70 transition-colors relative ${
              feed.status === "alert" ? "ring-2 ring-red-500/50" : ""
            }`}
          >
            <CardContent className="p-0">
              {/* Video Feed Area */}
              <div className="relative aspect-video bg-black rounded-t-lg overflow-hidden">
                {/* Mock Video Feed */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <Camera
                      className={`w-12 h-12 mx-auto mb-2 ${
                        feed.status === "online" ? "text-green-500" : "text-gray-500"
                      }`}
                    />
                    <p className="text-white text-sm font-medium">{feed.name}</p>
                    <p className="text-gray-300 text-xs">{feed.location}</p>
                  </div>
                </div>

                {/* Status Indicator */}
                <div className="absolute top-2 left-2">
                  <div className={`w-3 h-3 rounded-full ${getStatusColor(feed.status)}`} />
                </div>

                {/* Recording Indicator */}
                {feed.isRecording && (
                  <div className="absolute top-2 right-2 flex items-center gap-1">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                    <span className="text-white text-xs">REC</span>
                  </div>
                )}

                {/* AI Suggestion Overlay */}
                {feed.aiSuggestion && (
                  <div className="absolute bottom-2 left-2 right-2">
                    <div className="bg-blue-500/90 backdrop-blur-sm rounded px-2 py-1">
                      <p className="text-white text-xs">{feed.aiSuggestion}</p>
                    </div>
                  </div>
                )}

                <div className="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                  <Button size="icon" variant="secondary" className="w-8 h-8" onClick={() => handleViewCamera(feed.id)}>
                    <Maximize2 className="w-4 h-4" />
                  </Button>
                  <Button size="icon" variant="secondary" className="w-8 h-8" onClick={handlePlayPause}>
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button size="icon" variant="secondary" className="w-8 h-8">
                    {feed.hasAudio ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                  </Button>
                </div>
              </div>

              {/* Feed Info */}
              <div className="p-3">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-foreground text-sm">{feed.name}</h3>
                  <Badge variant={feed.status === "online" ? "default" : "destructive"} className="text-xs">
                    {feed.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{feed.location}</span>
                  <span>{feed.resolution}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground mt-1">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    <span>{feed.lastActivity}</span>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => toggleFeedSelection(feed.id)}
                    className={`h-6 px-2 ${selectedFeeds.includes(feed.id) ? "bg-blue-500/20 text-blue-400" : ""}`}
                  >
                    <Pin className="w-3 h-3" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Empty Slots */}
        {Array.from({ length: maxFeeds - displayFeeds.length }).map((_, index) => (
          <Card key={`empty-${index}`} className="bg-card/20 backdrop-blur-sm border-slate-600/30 border-dashed">
            <CardContent className="p-0">
              <div className="aspect-video flex items-center justify-center">
                <div className="text-center">
                  <Camera className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
                  <p className="text-muted-foreground text-sm">Empty Slot</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Fullscreen Modal */}
      {fullscreenFeed && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center">
          <div className="relative w-full h-full max-w-6xl max-h-4xl p-4">
            <Button
              className="absolute top-4 right-4 z-10"
              variant="secondary"
              size="icon"
              onClick={() => setFullscreenFeed(null)}
            >
              <X className="w-4 h-4" />
            </Button>
            <Card className="w-full h-full bg-card/95 backdrop-blur-sm">
              <CardContent className="p-0 h-full">
                <div className="relative h-full bg-black rounded-lg overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Camera className="w-24 h-24 text-green-500 mx-auto mb-4" />
                      <p className="text-white text-xl font-medium">
                        {allFeeds.find((f) => f.id === fullscreenFeed)?.name}
                      </p>
                      <p className="text-gray-300">{allFeeds.find((f) => f.id === fullscreenFeed)?.location}</p>
                    </div>
                  </div>

                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4">
                    {!isLive && (
                      <div className="mb-4">
                        <Slider
                          value={[progress]}
                          onValueChange={handleProgressChange}
                          max={100}
                          step={1}
                          className="w-full"
                        />
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                          <span>{currentTime}</span>
                          <span>{duration}</span>
                        </div>
                      </div>
                    )}

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <Button variant="secondary" onClick={handlePlayPause}>
                          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                        </Button>

                        {!isLive && (
                          <>
                            <Button variant="secondary" onClick={handleSkipBack}>
                              <SkipBack className="w-4 h-4" />
                            </Button>
                            <Button variant="secondary" onClick={handleSkipForward}>
                              <SkipForward className="w-4 h-4" />
                            </Button>
                          </>
                        )}

                        <Button variant="secondary" onClick={toggleMute}>
                          {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                        </Button>

                        <div className="text-white text-sm">
                          {isLive ? (
                            <div className="flex items-center gap-2">
                              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                              <span>LIVE</span>
                            </div>
                          ) : (
                            <span>{currentTime}</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {!isLive && (
                          <Button variant="secondary" onClick={handleGoLive} className="text-red-400">
                            <div className="w-2 h-2 bg-red-500 rounded-full mr-2" />
                            Go Live
                          </Button>
                        )}
                        <div className="text-white text-sm">
                          {allFeeds.find((f) => f.id === fullscreenFeed)?.resolution}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}

export { LiveFeedWall as default }
export type { CameraFeed }
