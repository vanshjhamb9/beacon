"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Skeleton } from "@/components/ui/skeleton"
import { Search, Download, Filter, Calendar, Mail, Phone, Building2, Star, Clock, CheckCircle2 } from "lucide-react"

const API_BASE = "/api/v1/ecommerce"

interface Lead {
  id: string
  company_name: string
  founder_name: string
  decision_maker_role: string
  email: string
  phone: string
  website: string
  city: string
  category: string
  lead_priority: string
  source: string
  created_at: string
}

export function TodayLeadsWorkspace() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [dateFilter, setDateFilter] = useState<string>("today")
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [priorityFilter, setPriorityFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [currentPage, setCurrentPage] = useState(1)
  const pageSize = 20

  const fetchLeads = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set("limit", "200")
      if (priorityFilter !== "all") params.set("priority", priorityFilter)

      const res = await fetch(`${API_BASE}/leads?${params}`)
      if (res.ok) {
        const data = await res.json()
        let filteredLeads = data.leads || []

        // Filter by date
        const today = new Date().toISOString().split('T')[0]
        if (dateFilter === "today") {
          filteredLeads = filteredLeads.filter((lead: Lead) => lead.created_at?.startsWith(today))
        } else if (dateFilter === "yesterday") {
          const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
          filteredLeads = filteredLeads.filter((lead: Lead) => lead.created_at?.startsWith(yesterday))
        } else if (dateFilter === "week") {
          const weekAgo = new Date(Date.now() - 7 * 86400000).toISOString().split('T')[0]
          filteredLeads = filteredLeads.filter((lead: Lead) => lead.created_at?.startsWith(weekAgo))
        }

        // Filter by status
        if (statusFilter === "new") {
          filteredLeads = filteredLeads.filter((lead: Lead) => lead.source === "comai_manual_import")
        } else if (statusFilter === "contacted") {
          filteredLeads = filteredLeads.filter((lead: Lead) => lead.source !== "comai_manual_import")
        }

        // Filter by search query
        if (searchQuery) {
          const query = searchQuery.toLowerCase()
          filteredLeads = filteredLeads.filter((lead: Lead) =>
            lead.company_name?.toLowerCase().includes(query) ||
            lead.email?.toLowerCase().includes(query) ||
            lead.founder_name?.toLowerCase().includes(query) ||
            lead.category?.toLowerCase().includes(query)
          )
        }

        setLeads(filteredLeads)
      }
    } catch (e) {
      console.error("Failed to fetch leads", e)
    } finally {
      setLoading(false)
    }
  }, [dateFilter, statusFilter, priorityFilter, searchQuery])

  useEffect(() => {
    fetchLeads()
  }, [fetchLeads])

  const paginatedLeads = leads.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  const stats = {
    total: leads.length,
    hot: leads.filter((l: Lead) => l.lead_priority === "HOT").length,
    warm: leads.filter((l: Lead) => l.lead_priority === "WARM").length,
    low: leads.filter((l: Lead) => l.lead_priority === "LOW").length,
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case "HOT":
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">HOT</Badge>
      case "WARM":
        return <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">WARM</Badge>
      case "LOW":
        return <Badge className="bg-gray-500/20 text-gray-400 border-gray-500/30">LOW</Badge>
      default:
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">{priority}</Badge>
    }
  }

  const getSourceBadge = (source: string) => {
    if (source === "comai_manual_import") {
      return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">New</Badge>
    }
    return <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">Contacted</Badge>
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Today's Leads</h1>
            <p className="text-muted-foreground">Qualified leads with email and phone contacts</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full bg-muted/20" />
          ))}
        </div>
        <Skeleton className="h-64 w-full bg-muted/20" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Today's Leads</h1>
          <p className="text-muted-foreground">Qualified leads with email and phone contacts</p>
        </div>
        <Button variant="outline" className="border-border/60">
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card/50 border-border/60">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>
        <Card className="bg-card/50 border-border/60">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hot Leads</CardTitle>
            <Star className="h-4 w-4 text-red-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-400">{stats.hot}</div>
          </CardContent>
        </Card>
        <Card className="bg-card/50 border-border/60">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warm Leads</CardTitle>
            <Clock className="h-4 w-4 text-yellow-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-400">{stats.warm}</div>
          </CardContent>
        </Card>
        <Card className="bg-card/50 border-border/60">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Low Priority</CardTitle>
            <CheckCircle2 className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-400">{stats.low}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-card/50 border-border/60">
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Date Filter */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Date</label>
              <Select value={dateFilter} onValueChange={setDateFilter}>
                <SelectTrigger className="bg-background/50 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="yesterday">Yesterday</SelectItem>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="all">All Time</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Status Filter */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Status</label>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="bg-background/50 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="new">New</SelectItem>
                  <SelectItem value="contacted">Contacted</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Priority Filter */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Priority</label>
              <Select value={priorityFilter} onValueChange={setPriorityFilter}>
                <SelectTrigger className="bg-background/50 border-border/60">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="HOT">Hot</SelectItem>
                  <SelectItem value="WARM">Warm</SelectItem>
                  <SelectItem value="LOW">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Search */}
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Search</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search leads..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-background/50 border-border/60"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leads Table */}
      <Card className="bg-card/50 border-border/60">
        <CardHeader>
          <CardTitle className="text-sm font-medium">
            Leads ({leads.length} total)
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full bg-muted/20" />
              ))}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow className="border-border/60">
                    <TableHead>Company</TableHead>
                    <TableHead>Contact</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Priority</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paginatedLeads.map((lead: Lead) => (
                    <TableRow key={lead.id} className="border-border/60 hover:bg-muted/20">
                      <TableCell className="font-medium">{lead.company_name}</TableCell>
                      <TableCell>
                        {lead.founder_name && (
                          <div>
                            <div className="text-sm">{lead.founder_name}</div>
                            {lead.decision_maker_role && (
                              <div className="text-xs text-muted-foreground">{lead.decision_maker_role}</div>
                            )}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Mail className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">{lead.email}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Phone className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">{lead.phone}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="border-border/60">{lead.category}</Badge>
                      </TableCell>
                      <TableCell>{getPriorityBadge(lead.lead_priority)}</TableCell>
                      <TableCell>{getSourceBadge(lead.source)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <p className="text-sm text-muted-foreground">
                  Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, leads.length)} of {leads.length} leads
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="border-border/60"
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage(p => Math.min(Math.ceil(leads.length / pageSize), p + 1))}
                    disabled={currentPage >= Math.ceil(leads.length / pageSize)}
                    className="border-border/60"
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
