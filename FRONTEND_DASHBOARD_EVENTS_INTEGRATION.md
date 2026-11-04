# Boatrider Sports — Frontend Implementation Prompt: Admin Dashboard Events & Registrations Module

> **Instruction for Frontend Developer / AI Agent:**  
> Implement the complete **Events & Registrations Management Module** in the **Boatrider Sports Admin Dashboard** (Next.js / React / Tailwind CSS).  
> This module allows staff to view, create, edit, publish/archive events, view live spot counters, manage attendee registrations, update rider attendance status, and export marshal-ready CSV lists.

---

## 1. System Overview & Backend Configuration

- **API Base URL:** `https://server.boatridersports.in/api` (or environment variable `NEXT_PUBLIC_API_URL`)
- **Authentication:** All admin endpoints require the superuser/staff JWT token:
  ```http
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
  *(Note: If your dashboard uses HTTP-only cookies, requests with `withCredentials: true` are also supported).*

### Supported API Routes:
Both `/api/dashboard/events/` and `/api/admin/events/` routes are supported:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/events/` | List all events with live metrics (`total_registrations`, `confirmed_riders`, `spots_left`) |
| `POST` | `/api/dashboard/events/` | Create a new event |
| `GET` | `/api/dashboard/events/<id>/` | Fetch single event record for editing |
| `PATCH` / `PUT` | `/api/dashboard/events/<id>/` | Update event details, change spot limits, toggle publish |
| `DELETE` | `/api/dashboard/events/<id>/` | Delete event (or pass query `?archive=true` to unpublish & cancel) |
| `GET` | `/api/dashboard/events/<id>/registrations/` | List all registered attendees for an event (search & status filter) |
| `PATCH` | `/api/dashboard/events/registrations/<id>/status/` | Update attendee status (`'confirmed'`, `'attended'`, `'cancelled'`, `'waitlist'`) |
| `GET` | `/api/dashboard/events/<id>/export-csv/` | Download marshal-ready CSV roster of registered riders |

---

## 2. TypeScript Data Interfaces

Create or add these definitions to your dashboard types directory (e.g., `types/events.ts`):

```typescript
export type EventCategory = 'Community' | 'Trail' | 'Race' | 'Workshop';
export type EventDifficulty = 'All Levels' | 'Beginner Friendly' | 'Intermediate' | 'Advanced' | 'Expert';
export type EventStatus = 'upcoming' | 'ongoing' | 'completed' | 'cancelled';
export type RegistrationStatus = 'confirmed' | 'waitlist' | 'attended' | 'cancelled';

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
```

---

## 3. API Client Integration Services

Implement the API calls in `services/dashboardEvents.ts`:

```typescript
import axios from 'axios';
import { DashboardEvent, EventRegistrationItem, RegistrationStatus } from '@/types/events';

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

  // 6. Get all registered riders for an event
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

  // 7. Update rider registration status (e.g. mark attended or cancelled)
  updateRegistrationStatus: async (registrationId: string, status: RegistrationStatus) => {
    const res = await axios.patch<{ success: boolean; message: string; data: EventRegistrationItem }>(
      `${API_BASE}/dashboard/events/registrations/${registrationId}/status/`,
      { status },
      getAuthHeaders()
    );
    return res.data;
  },

  // 8. Download Marshal CSV Export
  downloadAttendeesCsv: async (eventId: string, eventTitle: string) => {
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
  },
};
```

---

## 4. UI Specifications & Components

### 4.1. Events Management View (`/dashboard/events`)

1. **Top KPI Metrics Summary:**
   - **Total Events:** Total count of events.
   - **Active Upcoming Rides:** Events with `status === 'upcoming'` and `is_published === true`.
   - **Confirmed Riders:** Sum of `confirmed_riders`.
   - **Overall Capacity Filled:** Progress bar showing `(total filled_spots / total max_spots) * 100`.
2. **Filters & Controls:**
   - Real-time search bar (filters by title, location, description).
   - Category filter pills (`All`, `Community`, `Trail`, `Race`, `Workshop`).
   - Status dropdown (`All`, `Upcoming`, `Ongoing`, `Completed`, `Cancelled`).
   - **`+ Create New Event`** primary CTA button.
3. **Events Table:**
   - **Cover Image & Title:** Small rounded thumbnail, event title, tag badge (`Featured`, `Popular`).
   - **Date & Schedule:** Date & Time badge.
   - **Location:** Landmark and city with external Maps link icon.
   - **Category & Difficulty:** Pill badges (e.g., `Trail • Advanced`).
   - **Capacity Bar:** Progress indicator showing `filled_spots / max_spots` with green/amber badge for `spots_left`.
   - **Status Badge:**
     - `upcoming`: Blue / Indigo
     - `ongoing`: Green pulse
     - `completed`: Slate
     - `cancelled`: Red
   - **Publish Toggle:** Instant toggle switch bound to `PATCH { is_published: !current }`.
   - **Action Dropdown / Buttons:**
     - 👥 **`View Attendees`** (opens drawer/modal).
     - ✏️ **`Edit`** (opens event edit modal).
     - 📥 **`Download CSV`** (downloads rider roster).
     - 🗑️ **`Archive / Delete`** (triggers confirm modal).

---

### 4.2. Event Create / Edit Form Modal

Form fields mapped to the backend model:
- `title` (string, required)
- `category` (select: `Community`, `Trail`, `Race`, `Workshop`)
- `category_label` (string, e.g. "Hill Climb", "Coastal Brevet")
- `tag` (string, e.g. "Featured", "Championship")
- `date` (string, e.g. "Sat, Nov 28, 2026")
- `time` (string, e.g. "6:00 AM - 1:00 PM")
- `location` (string, required)
- `google_maps_url` (url, optional)
- `distance` (string, e.g. "65 km" or "3 Hours Workshop")
- `difficulty` (select: `All Levels`, `Beginner Friendly`, `Intermediate`, `Advanced`, `Expert`)
- `max_spots` (number, min: 1, default: 50)
- `fee` (string, default: "Free Entry")
- `is_free` (boolean checkbox, default: `true`)
- `image` (string URL or media uploader)
- `description` (textarea / rich text)
- `highlights` (tag chips list, e.g. `["1,200m Elevation Gain", "Finisher Medal"]`)
- `schedule` (dynamic key-value array of `{ time: string, activity: string }`)
- `status` (select: `upcoming`, `ongoing`, `completed`, `cancelled`)
- `is_published` (toggle switch, default: `true`)

---

### 4.3. Event Attendees & Registration Drawer (`/dashboard/events/[id]/attendees`)

When an admin clicks **`View Attendees`** on any event row:
1. **Header Panel:**
   - Event Title & Date subtitle.
   - Live Spot Counters:
     - Total Registrations (`total_registrations`)
     - Confirmed Riders (`confirmed_riders`)
     - Attended Riders (`attended_riders`)
     - Available Spots Left (`spots_left`)
   - **`📥 Export Marshal CSV`** CTA button (calls `downloadAttendeesCsv`).
2. **Search & Status Filters:**
   - Search input: Searches by Rider Name, Phone, Email, or Ticket Code.
   - Status Tabs: `All`, `Confirmed`, `Attended`, `Cancelled`, `Waitlist`.
3. **Attendee Roster Table:**
   - **Ticket Code:** Mono badge (e.g. `#BR-EVT-2026-5337`).
   - **Rider Info:** Full name, clickable phone (`tel:`) and email (`mailto:`).
   - **Slots Reserved:** Number of riders (e.g. `2 Riders`).
   - **Bike & Skill:** Bike type (`Road Bike`) + Experience (`Intermediate`).
   - **Emergency Contact:** Name & Phone.
   - **Notes:** Special requests or dietary requirements.
   - **Status Badge:**
     - `Confirmed` (Green badge)
     - `Attended` (Blue badge)
     - `Cancelled` (Grey/Red badge)
     - `Waitlist` (Amber badge)
   - **Quick Actions:**
     - **`Mark Attended`**: Updates status to `'attended'`.
     - **`Cancel Registration`**: Updates status to `'cancelled'`. **Automatically reclaims spot on the event.**
     - **`Re-confirm`**: Re-activates a cancelled registration if spots are open.

---

## 5. Critical Business Logic to Follow

1. **No Online Payment Step:**  
   Event registrations are directly confirmed without payment gateways (`payment_status = 'not_required'`). Do not display payment gateway buttons or pending transaction prompts for event attendees.
2. **Automatic Spot Reclamation:**  
   When a registration status is changed to `'cancelled'`, the backend automatically decrements `filled_spots` and reclaims available slots (`spots_left`). Invalidate or refresh the event data to reflect the updated capacity bar.
3. **Excel-Friendly CSV Export:**  
   The CSV endpoint includes UTF-8 Byte Order Mark (`\ufeff`). Use a blob download handler so Microsoft Excel opens special characters and formatting cleanly without character corruption.

---

## 6. Definition of Done (DoD)

- [ ] Dashboard displays list of events with live capacity progress bars (`filled_spots / max_spots`).
- [ ] Admin can create, edit, toggle publish, and archive/delete events.
- [ ] Clicking **"View Attendees"** opens the attendee drawer with real-time rider counts.
- [ ] Search filters attendees by name, phone, email, or ticket code.
- [ ] Admin can update attendee status (`confirmed` -> `attended` / `cancelled`).
- [ ] Cancelling a registration updates the event's spot count in real-time.
- [ ] 1-click **"Export CSV"** downloads the full rider roster formatted for event marshals.

