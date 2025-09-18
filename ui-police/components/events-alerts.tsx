"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import {
  AlertTriangle,
  Camera,
  Clock,
  MapPin,
  Search,
  Bell,
  BellRing,
  Eye,
  Play,
  Zap,
  Users,
  Car,
  Shield,
  CheckCircle,
  ArrowUp,
  Send,
  Download,
  Pin,
} from "lucide-react"

interface Event {
  id: string
  type: string
  severity: "low" | "medium" | "high" | "critical"
  title: string
  description: string
  camera: string
  location: string
  timestamp: string
  duration?: string
  aiConfidence: number
  status: "new" | "acknowledged" | "resolved"
  clusterId?: string
  relatedEvents?: number
}

interface EventCluster {
  id: string
  title: string
  description: string
  eventCount: number
  severity: "low" | "medium" | "high" | "critical"
  location: string
  timeRange: string
  events: Event[]
}

export function EventsAlerts() {
  const [filter, setFilter] = useState("all")
  const [severityFilter, setSeverityFilter] = useState("all")
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)
  const [viewMode, setViewMode] = useState<"timeline" | "clusters">("timeline")
  const [showActionMenu, setShowActionMenu] = useState<string | null>(null)
  const [actionFeedback, setActionFeedback] = useState<{ eventId: string; action: string; message: string } | null>(
    null,
  )

  // Mock events data
  const events: Event[] = [
    {
      id: "1",
      type: "Motion Detection",
      severity: "high",
      title: "Suspicious Activity Detected",
      description: "Person loitering near hospital entrance for extended period (12+ minutes)",
      camera: "Camera 24",
      location: "Hospital Main Entrance",
      timestamp: "2 minutes ago",
      duration: "12:34",
      aiConfidence: 0.94,
      status: "new",
      clusterId: "cluster-1",
      relatedEvents: 3,
    },
    {
      id: "2",
      type: "Unusual Behavior",
      severity: "critical",
      title: "Multiple Fights Detected",
      description: "AI detected aggressive behavior and potential altercation",
      camera: "Camera 12",
      location: "Sector 7 - Parking Area",
      timestamp: "5 minutes ago",
      duration: "3:45",
      aiConfidence: 0.89,
      status: "new",
      clusterId: "cluster-2",
      relatedEvents: 2,
    },
    {
      id: "3",
      type: "Perimeter Breach",
      severity: "high",
      title: "Unauthorized Access Attempt",
      description: "Person attempting to access restricted area after hours",
      camera: "Camera 8",
      location: "Emergency Exit B",
      timestamp: "8 minutes ago",
      aiConfidence: 0.91,
      status: "acknowledged",
    },
    {
      id: "4",
      type: "Vehicle Alert",
      severity: "medium",
      title: "Speeding Vehicle Detected",
      description: "Vehicle exceeding speed limit in hospital zone",
      camera: "Camera 15",
      location: "Hospital Driveway",
      timestamp: "12 minutes ago",
      aiConfidence: 0.87,
      status: "resolved",
    },
    {
      id: "5",
      type: "Crowd Detection",
      severity: "medium",
      title: "Large Gathering Detected",
      description: "Unusual crowd formation in normally quiet area",
      camera: "Camera 6",
      location: "Courtyard Area",
      timestamp: "18 minutes ago",
      aiConfidence: 0.82,
      status: "acknowledged",
      clusterId: "cluster-1",
    },
  ]

  // Mock clusters data
  const clusters: EventCluster[] = [
    {
      id: "cluster-1",
      title: "Suspicious Activity - Hospital Entrance",
      description: "Multiple related incidents near main entrance area",
      eventCount: 3,
      severity: "high",
      location: "Hospital Main Entrance Area",
      timeRange: "Last 20 minutes",
      events: events.filter((e) => e.clusterId === "cluster-1"),
    },
    {
      id: "cluster-2",
      title: "Security Incidents - Sector 7",
      description: "Escalating situation requiring immediate attention",
      eventCount: 2,
      severity: "critical",
      location: "Sector 7 - Parking Area",
      timeRange: "Last 10 minutes",
      events: events.filter((e) => e.clusterId === "cluster-2"),
    },
  ]

  const filteredEvents = events.filter((event) => {
    const matchesFilter = filter === "all" || event.status === filter
    const matchesSeverity = severityFilter === "all" || event.severity === severityFilter
    const matchesSearch =
      event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.location.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesFilter && matchesSeverity && matchesSearch
  })

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical":
        return "bg-red-500/20 text-red-400 border-red-500/30"
      case "high":
        return "bg-orange-500/20 text-orange-400 border-orange-500/30"
      case "medium":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      case "low":
        return "bg-blue-500/20 text-blue-400 border-blue-500/30"
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "new":
        return "bg-red-500/20 text-red-400 border-red-500/30"
      case "acknowledged":
        return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
      case "resolved":
        return "bg-green-500/20 text-green-400 border-green-500/30"
      default:
        return "bg-gray-500/20 text-gray-400 border-gray-500/30"
    }
  }

  const getEventIcon = (type: string) => {
    switch (type) {
      case "Motion Detection":
        return <Eye className="w-4 h-4" />
      case "Unusual Behavior":
        return <Users className="w-4 h-4" />
      case "Perimeter Breach":
        return <Shield className="w-4 h-4" />
      case "Vehicle Alert":
        return <Car className="w-4 h-4" />
      case "Crowd Detection":
        return <Users className="w-4 h-4" />
      default:
        return <AlertTriangle className="w-4 h-4" />
    }
  }

  const handleTakeAction = (eventId: string, action: string) => {
    console.log(`Taking action: ${action} for event: ${eventId}`)
    setShowActionMenu(null)

    const actionMessages = {
      acknowledge: "Event marked as acknowledged",
      escalate: "Event escalated to higher authority",
      dispatch: "Patrol unit has been notified",
      export: "Evidence clip exported successfully",
      pin: "Event pinned to dashboard",
    }

    setActionFeedback({
      eventId,
      action,
      message: actionMessages[action as keyof typeof actionMessages] || "Action completed",
    })

    // Clear feedback after 3 seconds
    setTimeout(() => setActionFeedback(null), 3000)
  }

  const handleViewCamera = (eventId: string, cameraId: string) => {
    // This will be connected to the live feed functionality
    console.log(`Viewing camera ${cameraId} for event ${eventId}`)
    // You can add navigation to live feed with specific camera here
  }

  const handlePlayback = (eventId: string, timestamp: string) => {
    // This will be connected to the playback functionality
    console.log(`Playing back event ${eventId} from ${timestamp}`)
    // You can add navigation to playback with specific timestamp here
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Events & Alerts</h1>
          <p className="text-muted-foreground">AI-driven notifications and event monitoring</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" className="bg-transparent">
            <Bell className="w-4 h-4 mr-2" />
            Notifications
          </Button>
          <Button variant="outline" className="bg-transparent">
            <BellRing className="w-4 h-4 mr-2" />
            Live Alerts
          </Button>
        </div>
      </div>

      {/* AI Summary Card */}
      <Card className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/20">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-purple-400" />
            AI Event Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-400">2</div>
              <div className="text-sm text-muted-foreground">Critical Events</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-400">3</div>
              <div className="text-sm text-muted-foreground">High Priority</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">2</div>
              <div className="text-sm text-muted-foreground">Event Clusters</div>
            </div>
          </div>
          <div className="mt-4 p-3 bg-purple-500/10 rounded-lg">
            <p className="text-sm text-purple-200">
              <strong>AI Insight:</strong> Increased activity detected near Hospital Main Entrance. Multiple related
              incidents suggest coordinated suspicious behavior requiring immediate attention.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Search className="w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search events..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-64"
            />
          </div>
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="new">New</SelectItem>
              <SelectItem value="acknowledged">Acknowledged</SelectItem>
              <SelectItem value="resolved">Resolved</SelectItem>
            </SelectContent>
          </Select>
          <Select value={severityFilter} onValueChange={setSeverityFilter}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severity</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={viewMode === "timeline" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("timeline")}
            className={viewMode !== "timeline" ? "bg-transparent" : ""}
          >
            Timeline
          </Button>
          <Button
            variant={viewMode === "clusters" ? "default" : "outline"}
            size="sm"
            onClick={() => setViewMode("clusters")}
            className={viewMode !== "clusters" ? "bg-transparent" : ""}
          >
            Clusters
          </Button>
        </div>
      </div>

      {/* Action Feedback */}
      {actionFeedback && (
        <div className="fixed top-4 right-4 z-50">
          <Card className="bg-green-500/20 border-green-500/30">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-sm text-green-400">{actionFeedback.message}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Event Clusters View */}
      {viewMode === "clusters" && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">AI Event Clusters</h2>
          {clusters.map((cluster) => (
            <Card key={cluster.id} className="bg-card/50 backdrop-blur-sm border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle
                      className={`w-5 h-5 ${cluster.severity === "critical" ? "text-red-500" : "text-orange-500"}`}
                    />
                    {cluster.title}
                  </CardTitle>
                  <Badge variant="outline" className={getSeverityColor(cluster.severity)}>
                    {cluster.severity.toUpperCase()}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground mb-4">{cluster.description}</p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground">{cluster.location}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground">{cluster.timeRange}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm text-foreground">{cluster.eventCount} events</span>
                  </div>
                </div>
                <div className="space-y-2">
                  {cluster.events.slice(0, 2).map((event) => (
                    <div key={event.id} className="p-2 bg-muted/20 rounded-lg text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-foreground">{event.title}</span>
                        <span className="text-muted-foreground">{event.timestamp}</span>
                      </div>
                    </div>
                  ))}
                  {cluster.eventCount > 2 && (
                    <Button variant="ghost" size="sm" className="w-full">
                      View {cluster.eventCount - 2} more events
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Timeline View */}
      {viewMode === "timeline" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-foreground">Event Timeline</h2>
            <Badge variant="secondary">{filteredEvents.length} events</Badge>
          </div>

          {filteredEvents.map((event) => (
            <Card
              key={event.id}
              className={`bg-card/50 backdrop-blur-sm border-slate-700/50 hover:bg-card/70 transition-colors cursor-pointer ${
                event.severity === "critical" ? "ring-1 ring-red-500/30" : ""
              }`}
              onClick={() => setSelectedEvent(event)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  {/* Event Icon */}
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      event.severity === "critical"
                        ? "bg-red-500/20"
                        : event.severity === "high"
                          ? "bg-orange-500/20"
                          : event.severity === "medium"
                            ? "bg-yellow-500/20"
                            : "bg-blue-500/20"
                    }`}
                  >
                    {getEventIcon(event.type)}
                  </div>

                  {/* Event Details */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-foreground">{event.title}</h3>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className={getSeverityColor(event.severity)}>
                          {event.severity}
                        </Badge>
                        <Badge variant="outline" className={getStatusColor(event.status)}>
                          {event.status}
                        </Badge>
                      </div>
                    </div>

                    <p className="text-muted-foreground text-sm mb-3">{event.description}</p>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-sm">
                      <div className="flex items-center gap-2">
                        <Camera className="w-4 h-4 text-muted-foreground" />
                        <span className="text-foreground">{event.camera}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-muted-foreground" />
                        <span className="text-foreground">{event.location}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-muted-foreground" />
                        <span className="text-foreground">{event.timestamp}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-muted-foreground" />
                        <span className="text-foreground">AI: {Math.round(event.aiConfidence * 100)}%</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 mt-3">
                      <Button
                        size="sm"
                        variant="outline"
                        className="bg-transparent"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleViewCamera(event.id, event.camera)
                        }}
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        View Camera
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="bg-transparent"
                        onClick={(e) => {
                          e.stopPropagation()
                          handlePlayback(event.id, event.timestamp)
                        }}
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Playback
                      </Button>
                      <div className="relative">
                        <Button
                          size="sm"
                          variant="outline"
                          className="bg-blue-500/20 border-blue-500/30 text-blue-400 hover:bg-blue-500/30"
                          onClick={(e) => {
                            e.stopPropagation()
                            setShowActionMenu(showActionMenu === event.id ? null : event.id)
                          }}
                        >
                          <AlertTriangle className="w-4 h-4 mr-2" />
                          Take Action
                        </Button>

                        {showActionMenu === event.id && (
                          <div className="absolute top-full left-0 mt-1 w-48 bg-background border border-slate-700/50 rounded-lg shadow-lg z-50">
                            <div className="p-1">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="w-full justify-start text-left hover:bg-slate-700/50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleTakeAction(event.id, "acknowledge")
                                }}
                              >
                                <CheckCircle className="w-4 h-4 mr-2" />
                                Acknowledge
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="w-full justify-start text-left hover:bg-slate-700/50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleTakeAction(event.id, "escalate")
                                }}
                              >
                                <ArrowUp className="w-4 h-4 mr-2" />
                                Escalate
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="w-full justify-start text-left hover:bg-slate-700/50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleTakeAction(event.id, "dispatch")
                                }}
                              >
                                <Send className="w-4 h-4 mr-2" />
                                Dispatch
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="w-full justify-start text-left hover:bg-slate-700/50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleTakeAction(event.id, "export")
                                }}
                              >
                                <Download className="w-4 h-4 mr-2" />
                                Export Clip
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                className="w-full justify-start text-left hover:bg-slate-700/50"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleTakeAction(event.id, "pin")
                                }}
                              >
                                <Pin className="w-4 h-4 mr-2" />
                                Pin to Dashboard
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>

                      {event.relatedEvents && (
                        <Button size="sm" variant="outline" className="bg-transparent">
                          <AlertTriangle className="w-4 h-4 mr-2" />
                          {event.relatedEvents} Related
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}

          {filteredEvents.length === 0 && (
            <Card className="bg-card/50 backdrop-blur-sm border-slate-700/50">
              <CardContent className="py-12 text-center">
                <AlertTriangle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-medium text-foreground mb-2">No events found</h3>
                <p className="text-muted-foreground">Try adjusting your filters or search criteria.</p>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
