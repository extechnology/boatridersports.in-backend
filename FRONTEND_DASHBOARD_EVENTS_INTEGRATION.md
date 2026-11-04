# Boatrider Sports — Frontend Implementation Prompt: Admin Dashboard Events & Total Registrations Module

> **Instruction for Frontend Developer / AI Agent:**  
> Implement the complete **Events & Registrations Management Module** in the **Boatrider Sports Admin Dashboard** (Next.js / React / Tailwind CSS).  
> This module allows staff to:
> 1. View, create, edit, publish/archive cycling events and live spot counters.
> 2. View event attendees for individual events and update attendance status.
> 3. **View ALL event registration applications across all events in a unified table with search and filters.**
> 4. **Download the TOTAL event applications data in Excel (`.csv` with UTF-8 BOM)** either globally or filtered by event, date range, or status.
> 
> ⚠️ **CRITICAL REMINDER:** Event registrations do not require online payment (`payment_status = 'not_required'`). Do not show payment gateway modals or transaction checkouts for event riders.

---

## 1. System Overview & Backend Endpoints

- **API Base URL:** `https://server.boatridersports.in/api` (or environment variable `NEXT_PUBLIC_API_URL`)
- **Authentication:** All admin endpoints require the superuser/staff JWT token:
  ```http
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
  *(Note: If your dashboard uses HTTP-only cookies, requests with `withCredentials: true` are also supported).*

### Supported API Routes:
Both `/api/dashboard/events/` and `/api/admin/events/` base paths are supported:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/events/` | List all events with live metrics (`total_registrations`, `confirmed_riders`, `spots_left`) |
| `POST` | `/api/dashboard/events/` | Create a new event |
| `GET` | `/api/dashboard/events/<id>/` | Fetch single event record for editing |
| `PATCH` / `PUT` | `/api/dashboard/events/<id>/` | Update event details, change spot limits, toggle publish |
| `DELETE` | `/api/dashboard/events/<id>/` | Delete event (or pass query `?archive=true` to unpublish & cancel) |
| `GET` | `/api/dashboard/events/total-registrations/` (or `registrations/all/`) | **List ALL registrations across all events** with KPI summary, search & filters |
| `GET` | `/api/dashboard/events/export-excel/` | **Download TOTAL event applications in Excel format (`.csv` with UTF-8 BOM)** |
| `GET` | `/api/dashboard/events/<id>/registrations/` | List all registered attendees for a specific event |
| `PATCH` | `/api/dashboard/events/registrations/<id>/status/` | Update attendee status (`'confirmed'`, `'attended'`, `'cancelled'`, `'waitlist'`) |
| `GET` | `/api/dashboard/events/<id>/export-csv/` (or `<id>/export-excel/`) | Download marshal-ready Excel/CSV roster for a single event |

---

## 2. TypeScript Data Interfaces

Create or add these definitions to your dashboard types directory (e.g. `types/events.ts`):

```typescript
export type EventCategory = 'Community' | 'Trail' | 'Race' | 'Workshop';
export type EventDifficulty = 'All Levels' | 'Beginner Friendly' | 'Intermediate' | 'Advanced' | 'Expert';
export type EventStatus = 'upcoming' | 'ongoing' | 'completed' | 'cancelled';
export type RegistrationStatus = 'confirmed' | 'waitlist' | 'attended' | 'cancelled';
export type RegistrationTimeFilter = 'all_time' | 'today' | 'this_week' | 'this_month' | 'this_year' | 'custom';

export interface ScheduleItem {
  time: string;
  activity: string;
}

export interface DashboardEvent {
  id: string; // e.g. "wayanad-ghats-challenge"
  title: string;
  slug: string;
  category: EventCategory;
  category_label: string;
  tag: string;
  date: string; // e.g. "Sat, Nov 28, 2026"
  time: string; // e.g. "6:00 AM - 1:00 PM"
  location: string;
  google_maps_url?: string | null;
  distance: string; // e.g. "65 km" or "3 Hours Workshop"
  difficulty: EventDifficulty;
  fee: string; // e.g. "Free Entry"
  is_free: boolean;
  max_spots: number;
  filled_spots: number;
  spots_left: number;
  total_registrations: number;
  confirmed_riders: number;
  attended_riders: number;
  cancelled_count: number;
  image: string;
  description: string;
  highlights: string[];
  schedule: ScheduleItem[];
  status: EventStatus;
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface EventRegistrationItem {
  id: string; // UUID
  registration_number: string; // Ticket code, e.g. "BR-EVT-2026-5337"
  ticket_code: string;
  event: string;
  event_id: string;
  event_title: string;
  event_date?: string;
  event_time?: string;
  event_location?: string;
  event_category?: string;
  event_category_label?: string;
  full_name: string;
  phone: string;
  email: string;
  participants: number;
  bike_type: string;
  experience_level: string;
  emergency_contact: string;
  notes: string;
  agreed_to_terms: boolean;
  status: RegistrationStatus;
  payment_status: 'not_required' | 'paid' | 'pending' | 'waived';
  created_at: string;
  updated_at: string;
}

export interface RegistrationsSummaryKPIs {
  totalApplications: number;
  totalRiders: number;
  confirmedRiders: number;
  attendedRiders: number;
  cancelledRiders: number;
  waitlistRiders: number;
}

export interface PaginatedRegistrationsResponse {
  count: number;
  total_pages?: number;
  current_page?: number;
  next?: string | null;
  previous?: string | null;
  results: EventRegistrationItem[];
  summary: RegistrationsSummaryKPIs;
}
```

---

## 3. API Client Integration Services

Implement or update the API calls in `services/dashboardEvents.ts`:

```typescript
import axios from 'axios';
import { 
  DashboardEvent, 
  EventRegistrationItem, 
  PaginatedRegistrationsResponse, 
  RegistrationStatus,
  RegistrationTimeFilter 
} from '@/types/events';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://server.boatridersports.in/api';

const getAuthHeaders = () => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : '';
  return {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    withCredentials: true,
  };
};

export const dashboardEventsApi = {
  // 1. List events (with search, category, status, and pagination toggles)
  getEvents: async (params?: { search?: string; category?: string; status?: string; paginate?: boolean; page?: number }) => {
    const res = await axios.get<{ count: number; data: DashboardEvent[] }>(
      `${API_BASE}/dashboard/events/`,
      { ...getAuthHeaders(), params: { paginate: false, ...params } }
    );
    return res.data;
  },

  // 2. Fetch single event details for editing
  getEvent: async (id: string) => {
    const res = await axios.get<{ success: boolean; data: DashboardEvent }>(
      `${API_BASE}/dashboard/events/${id}/`,
      getAuthHeaders()
    );
    return res.data.data;
  },

  // 3. Create a new event
  createEvent: async (payload: Partial<DashboardEvent>) => {
    const res = await axios.post<{ success: boolean; message: string; data: DashboardEvent }>(
      `${API_BASE}/dashboard/events/`,
      payload,
      getAuthHeaders()
    );
    return res.data;
  },

  // 4. Update an existing event (partial patch)
  updateEvent: async (id: string, payload: Partial<DashboardEvent>) => {
    const res = await axios.patch<{ success: boolean; message: string; data: DashboardEvent }>(
      `${API_BASE}/dashboard/events/${id}/`,
      payload,
      getAuthHeaders()
    );
    return res.data;
  },

  // 5. Delete or Archive an event
  deleteEvent: async (id: string, archiveOnly = false) => {
    const res = await axios.delete<{ success: boolean; message: string }>(
      `${API_BASE}/dashboard/events/${id}/`,
      { ...getAuthHeaders(), params: archiveOnly ? { archive: true } : {} }
    );
    return res.data;
  },

  // 6. Get TOTAL event applications across ALL events (with pagination & KPI summary)
  getTotalRegistrations: async (params?: {
    search?: string;
    event_id?: string;
    category?: string;
    status?: string;
    filter?: RegistrationTimeFilter;
    start_date?: string; // YYYY-MM-DD
    end_date?: string;   // YYYY-MM-DD
    page?: number;
    paginate?: boolean;
  }) => {
    const res = await axios.get<PaginatedRegistrationsResponse>(
      `${API_BASE}/dashboard/events/total-registrations/`,
      { ...getAuthHeaders(), params }
    );
    return res.data;
  },

  // 7. Download TOTAL event applications in Excel (across all events or filtered)
  downloadAllRegistrationsExcel: async (params?: {
    search?: string;
    event_id?: string;
    category?: string;
    status?: string;
    filter?: RegistrationTimeFilter;
    start_date?: string;
    end_date?: string;
  }) => {
    const res = await axios.get(`${API_BASE}/dashboard/events/export-excel/`, {
      ...getAuthHeaders(),
      params,
      responseType: 'blob',
    });

    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = params?.event_id 
      ? `event_${params.event_id}_applications_${timestamp}.csv` 
      : `boatrider_all_event_applications_${timestamp}.csv`;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // 8. Get attendees for a single specific event
  getEventRegistrations: async (eventId: string, params?: { search?: string; status?: string }) => {
    const res = await axios.get<{
      success: boolean;
      eventId: string;
      eventTitle: string;
      totalRegistrations: number;
      data: EventRegistrationItem[];
    }>(`${API_BASE}/dashboard/events/${eventId}/registrations/`, {
      ...getAuthHeaders(),
      params,
    });
    return res.data;
  },

  // 9. Update attendee status (confirmed, attended, cancelled, waitlist)
  updateRegistrationStatus: async (registrationId: string, status: RegistrationStatus) => {
    const res = await axios.patch<{ success: boolean; message: string; data: EventRegistrationItem }>(
      `${API_BASE}/dashboard/events/registrations/${registrationId}/status/`,
      { status },
      getAuthHeaders()
    );
    return res.data;
  },

  // 10. Download single event marshal CSV
  downloadSingleEventAttendeesCsv: async (eventId: string, eventTitle: string) => {
    const res = await axios.get(`${API_BASE}/dashboard/events/${eventId}/export-csv/`, {
      ...getAuthHeaders(),
      responseType: 'blob',
    });
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${eventTitle.toLowerCase().replace(/\s+/g, '_')}_attendees.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};
```

---

## 4. UI Dashboard Structure & Views

The dashboard Events module should have two primary tabs:
1. **`Events Management` Tab**: Create, edit, toggle publish, view spot progress bars, and see per-event actions.
2. **`All Applications / Registrations` Tab**: Unified list of all registered applicants across all events with search, date filters, and the prominent **"Download All Applications (Excel)"** button.

### 4.1. "All Applications / Registrations" View Specifications

```tsx
// Example layout: app/(dashboard)/dashboard/events/page.tsx or components/events/AllApplicationsTab.tsx

import React, { useState, useEffect } from 'react';
import { dashboardEventsApi } from '@/services/dashboardEvents';
import { EventRegistrationItem, RegistrationsSummaryKPIs } from '@/types/events';

export default function AllApplicationsTab() {
  const [applications, setApplications] = useState<EventRegistrationItem[]>([]);
  const [summary, setSummary] = useState<RegistrationsSummaryKPIs | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [timeFilter, setTimeFilter] = useState('all_time');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await dashboardEventsApi.getTotalRegistrations({
        search,
        status: statusFilter,
        filter: timeFilter as any,
        page,
        paginate: true,
      });
      setApplications(data.results || []);
      setSummary(data.summary);
      setTotalPages(data.total_pages || 1);
    } catch (err) {
      console.error('Failed to fetch applications', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [search, statusFilter, timeFilter, page]);

  const handleExportExcel = async () => {
    setDownloading(true);
    try {
      await dashboardEventsApi.downloadAllRegistrationsExcel({
        search,
        status: statusFilter,
        filter: timeFilter as any,
      });
    } catch (err) {
      alert('Failed to download Excel file. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  const handleStatusChange = async (regId: string, newStatus: any) => {
    try {
      await dashboardEventsApi.updateRegistrationStatus(regId, newStatus);
      fetchApplications(); // Refresh list & spot counters
    } catch (err) {
      alert('Failed to update status.');
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. TOP SUMMARY METRIC CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold">Total Applications</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{summary?.totalApplications ?? 0}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold">Total Riders</p>
          <p className="text-3xl font-bold text-indigo-600 mt-2">{summary?.totalRiders ?? 0}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold">Confirmed Spots</p>
          <p className="text-3xl font-bold text-emerald-600 mt-2">{summary?.confirmedRiders ?? 0}</p>
        </div>
        <div className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm">
          <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold">Attended Riders</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">{summary?.attendedRiders ?? 0}</p>
        </div>
      </div>

      {/* 2. CONTROLS BAR: SEARCH, FILTERS & DOWNLOAD EXCEL BUTTON */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-gray-100 shadow-sm">
        <div className="flex flex-1 items-center gap-3">
          <input
            type="text"
            placeholder="Search by Rider Name, Phone, Email, Ticket #, or Event..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full md:w-96 px-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
          />
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 border rounded-lg text-sm text-gray-700 focus:outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="confirmed">Confirmed</option>
            <option value="attended">Attended</option>
            <option value="cancelled">Cancelled</option>
            <option value="waitlist">Waitlist</option>
          </select>
          <select
            value={timeFilter}
            onChange={(e) => { setTimeFilter(e.target.value); setPage(1); }}
            className="px-3 py-2 border rounded-lg text-sm text-gray-700 focus:outline-none"
          >
            <option value="all_time">All Time</option>
            <option value="today">Today</option>
            <option value="this_week">This Week</option>
            <option value="this_month">This Month</option>
            <option value="this_year">This Year</option>
          </select>
        </div>

        {/* PROMINENT DOWNLOAD EXCEL CTA BUTTON */}
        <button
          onClick={handleExportExcel}
          disabled={downloading}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm rounded-lg shadow-sm transition disabled:opacity-50"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {downloading ? 'Generating Excel...' : 'Download Total Applications (Excel)'}
        </button>
      </div>

      {/* 3. APPLICATIONS ROSTER TABLE */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-x-auto">
        <table className="w-full text-left text-sm text-gray-600">
          <thead className="bg-gray-50 text-xs uppercase tracking-wider text-gray-500 border-b">
            <tr>
              <th className="px-4 py-3">Ticket / Date</th>
              <th className="px-4 py-3">Event Details</th>
              <th className="px-4 py-3">Rider Info</th>
              <th className="px-4 py-3">Riders</th>
              <th className="px-4 py-3">Bike & Level</th>
              <th className="px-4 py-3">Emergency Contact</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {applications.map((app) => (
              <tr key={app.id} className="hover:bg-gray-50/60">
                <td className="px-4 py-3">
                  <div className="font-mono text-xs font-bold text-gray-800">{app.ticket_code}</div>
                  <div className="text-xs text-gray-400 mt-0.5">
                    {new Date(app.created_at).toLocaleDateString()}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="font-medium text-gray-900">{app.event_title}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{app.event_date} • {app.event_location}</div>
                </td>
                <td className="px-4 py-3">
                  <div className="font-semibold text-gray-900">{app.full_name}</div>
                  <div className="text-xs text-indigo-600">{app.phone}</div>
                  <div className="text-xs text-gray-400">{app.email}</div>
                </td>
                <td className="px-4 py-3 font-semibold text-gray-800">
                  {app.participants} {app.participants > 1 ? 'Riders' : 'Rider'}
                </td>
                <td className="px-4 py-3">
                  <div>{app.bike_type}</div>
                  <div className="text-xs text-gray-400">{app.experience_level}</div>
                </td>
                <td className="px-4 py-3 text-xs text-gray-600">
                  {app.emergency_contact || 'None provided'}
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                    app.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                    app.status === 'attended' ? 'bg-blue-100 text-blue-800' :
                    app.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                    'bg-amber-100 text-amber-800'
                  }`}>
                    {app.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-right space-x-1">
                  {app.status !== 'attended' && (
                    <button
                      onClick={() => handleStatusChange(app.id, 'attended')}
                      className="px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50 rounded"
                    >
                      Mark Attended
                    </button>
                  )}
                  {app.status !== 'cancelled' && (
                    <button
                      onClick={() => handleStatusChange(app.id, 'cancelled')}
                      className="px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 rounded"
                    >
                      Cancel
                    </button>
                  )}
                  {app.status === 'cancelled' && (
                    <button
                      onClick={() => handleStatusChange(app.id, 'confirmed')}
                      className="px-2 py-1 text-xs font-medium text-emerald-600 hover:bg-emerald-50 rounded"
                    >
                      Restore
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {applications.length === 0 && !loading && (
              <tr>
                <td colSpan={8} className="text-center py-12 text-gray-400">
                  No event applications found matching the selected filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

---

## 5. Critical Technical Rules

1. **UTF-8 BOM in Excel Export:**  
   The backend injects `\ufeff` (Byte Order Mark) into all `.csv` downloads. When downloading in React/Next.js via Axios, specify `responseType: 'blob'` and create the Blob with `type: 'text/csv;charset=utf-8;'` to guarantee proper column layout and font encoding in Microsoft Excel on Windows and macOS.
2. **Instant Spot Re-calculation:**  
   Cancelling or restoring a registration triggers an atomic adjustment of the parent event's `filled_spots`. When an admin marks an application `'cancelled'` or `'confirmed'`, invalidate React Query / SWR / local state for both the registration list and the events list so spot counters stay in sync.
3. **No Payment Gateway / Free Entry:**  
   The system confirms registrations directly (`payment_status = 'not_required'`). There is no online payment required.

---

## 6. Definition of Done (DoD)

- [ ] Admin dashboard has an **"All Applications / Total Registrations"** view displaying registrations across all events.
- [ ] Top KPI cards display Total Applications, Total Riders, Confirmed Spots, and Attended Riders.
- [ ] Admin can filter by Search text (Rider Name, Phone, Email, Ticket #, Event Title), Status, and Time Filter.
- [ ] **"Download Total Applications (Excel)"** button streams the complete formatted `.csv` file directly to the user's downloads folder.
- [ ] Single event view retains its individual **"Export Marshal CSV"** button.
- [ ] Admin can change attendee status (`confirmed` -> `attended` / `cancelled`), updating event spot counters immediately.
