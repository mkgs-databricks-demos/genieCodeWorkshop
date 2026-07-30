# WanderBricks Analytics Handbook

> **Version:** 1.0  
> **Last Updated:** 2026-07-30  
> **Owner:** WanderBricks Data & Analytics Team  
> **Status:** Approved for implementation

This document defines the official business metrics, KPIs, rules, and SLAs for the WanderBricks platform. All analytics implementations, dashboards, and reports must conform to these definitions.

---

## 1. Revenue Metrics

### 1.1 Gross Booking Value (GBV)

**Definition:** The total monetary value of all confirmed bookings in a given period, before any deductions.

**Calculation:**
```
GBV = SUM(total_amount) WHERE status = 'confirmed'
```

**Source table:** `bookings`  
**Grain:** Per booking  
**Time dimension:** `created_at` (booking creation date, not check-in date)

### 1.2 Net Revenue

**Definition:** Platform revenue after host payouts. WanderBricks retains a 15% platform commission on all confirmed bookings.

**Calculation:**
```
Net Revenue = GBV × 0.15
Host Payout = GBV × 0.85
```

**Commission structure:**
- Standard commission: 15% of `total_amount`
- No tiered pricing at this time
- Commission applies only to `status = 'confirmed'` bookings

### 1.3 Average Daily Rate (ADR)

**Definition:** The average revenue earned per booked night across all properties.

**Calculation:**
```
ADR = SUM(total_amount) / SUM(DATEDIFF(check_out, check_in))
     WHERE status IN ('confirmed', 'completed')
```

**Exclusions:** Cancelled and pending bookings are excluded from ADR calculation.

### 1.4 Revenue Per Available Night (RevPAN)

**Definition:** Total revenue divided by total available nights across all listed properties. This measures how effectively inventory is being monetized.

**Calculation:**
```
RevPAN = Net Revenue / Total Available Nights
Total Available Nights = COUNT(DISTINCT properties) × days_in_period
```

---

## 2. Occupancy & Utilization Metrics

### 2.1 Occupancy Rate

**Definition:** The percentage of available property-nights that are booked in a given period.

**Calculation:**
```
Occupancy Rate = Booked Nights / Available Nights

Booked Nights = SUM(DATEDIFF(check_out, check_in))
               WHERE status IN ('confirmed', 'completed')
               AND check_in >= period_start
               AND check_in < period_end

Available Nights = COUNT(DISTINCT property_id WHERE created_at <= period_end) × days_in_period
```

**Target:** 65% occupancy rate platform-wide  
**Segmentation:** Always report by `property_type` and `destination_id`

### 2.2 Booking Lead Time

**Definition:** The number of days between booking creation and check-in date.

**Calculation:**
```
Booking Lead Time = DATEDIFF(check_in, DATE(created_at))
```

**Benchmarks:**
- Short-term: < 7 days ("last minute")
- Medium-term: 7–30 days
- Long-term: > 30 days ("advance planners")

### 2.3 Average Length of Stay (ALOS)

**Definition:** The average number of nights per booking.

**Calculation:**
```
ALOS = AVG(DATEDIFF(check_out, check_in))
       WHERE status IN ('confirmed', 'completed')
```

---

## 3. Guest Satisfaction Metrics

### 3.1 Guest Satisfaction Score (GSS)

**Definition:** Weighted average of all review ratings, with recency bias applied.

**Calculation:**
```
GSS = SUM(rating × recency_weight) / SUM(recency_weight)

recency_weight:
  - Reviews in last 30 days: weight = 3.0
  - Reviews in last 90 days: weight = 2.0
  - Reviews in last 365 days: weight = 1.0
  - Reviews older than 365 days: weight = 0.5

WHERE is_deleted = false
```

**Scale:** 1.0 to 5.0  
**Target:** Platform-wide GSS ≥ 4.2  
**Reporting grain:** Per property, per destination, platform-wide

### 3.2 Review Response Rate

**Definition:** Percentage of bookings that result in a guest review.

**Calculation:**
```
Review Response Rate = COUNT(DISTINCT reviews.booking_id) / COUNT(DISTINCT bookings.booking_id)
                      WHERE bookings.status = 'confirmed'
                      AND bookings.check_out < CURRENT_DATE
```

**Target:** ≥ 40% of completed stays should generate a review

### 3.3 Negative Review Rate

**Definition:** Percentage of reviews with rating below 3.0.

**Calculation:**
```
Negative Review Rate = COUNT(reviews WHERE rating < 3.0 AND is_deleted = false)
                     / COUNT(reviews WHERE is_deleted = false)
```

**Alert threshold:** > 20% negative reviews for any property triggers review

---

## 4. Host Performance Metrics

### 4.1 Superhost Status

**Definition:** A designation for hosts who consistently deliver exceptional guest experiences.

**Criteria (ALL must be met):**
```
1. Average rating ≥ 4.5 (across all properties, trailing 90 days)
2. Completed bookings ≥ 10 (trailing 90 days)
3. Cancellation rate < 2% (host-initiated cancellations)
4. Response rate ≥ 90% (responded to booking requests within 24 hours)
```

**Evaluation frequency:** Monthly  
**Grace period:** Hosts losing superhost status have 30 days to regain it before badge removal

### 4.2 Host Response Time

**Definition:** Time between a guest inquiry/booking request and the host's first response.

**SLA:**
- Target: < 24 hours for initial response
- Critical: > 48 hours triggers automated follow-up
- Measured from: `booking_updates` table (first status change after booking creation)

### 4.3 Host Cancellation Rate

**Definition:** Percentage of confirmed bookings cancelled by the host.

**Calculation:**
```
Host Cancellation Rate = COUNT(bookings WHERE status = 'cancelled_by_host')
                       / COUNT(bookings WHERE status IN ('confirmed', 'completed', 'cancelled_by_host'))
```

**Note:** In the current data model, cancellations are reflected in `booking_updates` table with status changes. Distinguish host-initiated vs guest-initiated via the `booking_updates` metadata.

---

## 5. Platform Operations Metrics

### 5.1 Support Ticket Volume

**Definition:** Number of customer support tickets created per period.

**Source:** `customer_support_logs`  
**Segmentation by issue type:** Determined by analyzing the first user message in the `messages` array using the following taxonomy:

| Category | Keywords/Patterns |
| --- | --- |
| Booking Issues | double-booking, cancellation, modification, refund |
| Payment Issues | payout, payment, charge, refund processing |
| Property Issues | cleanliness, damage, not as described, maintenance |
| Safety Issues | emergency, unsafe, security concern |
| Account Issues | login, verification, profile, password |

### 5.2 Support Resolution Time

**Definition:** Time from ticket creation to final agent response.

**Calculation:**
```
Resolution Time = MAX(messages.timestamp) - MIN(messages.timestamp)
                 WHERE messages.sender = 'agent' (for the final message)
```

**SLA:**
- P1 (Safety): Resolution within 4 hours
- P2 (Active booking affected): Resolution within 24 hours  
- P3 (General): Resolution within 72 hours

### 5.3 Customer Satisfaction (CSAT) for Support

**Definition:** Derived from the sentiment of the user's final message in a support thread.

**Calculation:**
```
Positive resolution: final user message sentiment IN ('positive', 'optimistic', 'grateful')
Negative resolution: final user message sentiment IN ('angry', 'negative', 'frustrated')
Neutral: all other sentiments

CSAT = COUNT(positive resolutions) / COUNT(all resolutions)
```

**Target:** ≥ 75% positive resolution rate

---

## 6. Engagement & Conversion Metrics

### 6.1 Search-to-Book Conversion Rate

**Definition:** Percentage of search sessions that result in a confirmed booking.

**Calculation:**
```
Conversion Rate = COUNT(DISTINCT sessions with booking) 
               / COUNT(DISTINCT sessions with search event)

Session definition: All clickstream events from same user_id within 30-minute inactivity window
```

**Source:** `clickstream` table (events: search, view, click, filter)  
**Segmentation:** By device type (`metadata.device`) and referrer (`metadata.referrer`)

### 6.2 Property View-to-Book Rate

**Definition:** Percentage of property views that convert to a booking.

**Calculation:**
```
View-to-Book = COUNT(DISTINCT bookings.property_id, bookings.user_id)
             / COUNT(DISTINCT clickstream.property_id, clickstream.user_id
                     WHERE event = 'view')
```

### 6.3 Bounce Rate by Referrer

**Definition:** Percentage of sessions with only one event (single-page sessions).

**Calculation:**
```
Bounce Rate = COUNT(sessions with exactly 1 event) / COUNT(all sessions)
```

**Segmentation:** Always report by `metadata.referrer` (google, direct, email, ad)

---

## 7. Inventory & Supply Metrics

### 7.1 Active Listings

**Definition:** Properties that have received at least one booking in the trailing 90 days OR were created within the last 30 days.

**Calculation:**
```
Active Listings = COUNT(DISTINCT property_id)
                 WHERE property_id IN (
                   SELECT property_id FROM bookings 
                   WHERE created_at >= CURRENT_DATE - INTERVAL 90 DAYS
                 )
                 OR property_id IN (
                   SELECT property_id FROM properties
                   WHERE created_at >= CURRENT_DATE - INTERVAL 30 DAYS
                 )
```

### 7.2 New Listings

**Definition:** Properties listed for the first time in the reporting period.

**Source:** `properties.created_at`  
**Target:** 5% month-over-month growth in new listings

### 7.3 Listing Quality Score

**Definition:** A composite score indicating how complete and attractive a listing is.

**Calculation:**
```
Listing Quality Score (0-100) =
  + 20 points: description length > 100 characters
  + 20 points: has at least 3 images (property_images table)
  + 20 points: has at least 5 amenities listed (property_amenities table)
  + 20 points: has at least 3 reviews with avg rating >= 4.0
  + 20 points: base_price is within 20% of destination median
```

---

## 8. Geographic & Seasonal Metrics

### 8.1 Destination Performance Index (DPI)

**Definition:** Composite ranking of destinations based on demand, supply, and satisfaction.

**Calculation:**
```
DPI = (0.4 × normalized_occupancy_rate)
    + (0.3 × normalized_GBV)
    + (0.2 × normalized_GSS)
    + (0.1 × normalized_new_listings_growth)
```

**Grain:** Per `destination_id`, monthly  
**Join path:** `bookings` → `properties` → `destinations`

### 8.2 Seasonal Demand Index

**Definition:** Ratio of current period bookings to the trailing 12-month average for the same destination.

**Calculation:**
```
Seasonal Demand Index = current_period_bookings / avg_monthly_bookings_trailing_12m

> 1.0 = above-average demand (peak season)
< 1.0 = below-average demand (off season)
= 1.0 = average demand
```

---

## 9. Data Quality Rules

These rules must be enforced at the pipeline level (SDP expectations):

| Rule | Table | Condition | Action |
| --- | --- | --- | --- |
| Valid booking dates | `bookings` | `check_out > check_in` | Drop |
| Positive amounts | `bookings` | `total_amount > 0` | Drop |
| Valid guest count | `bookings` | `guests_count BETWEEN 1 AND max_guests` | Flag |
| Rating range | `reviews` | `rating BETWEEN 1.0 AND 5.0` | Fail |
| Non-empty reviews | `reviews` | `LENGTH(comment) > 0` | Drop |
| Valid coordinates | `properties` | `property_latitude BETWEEN -90 AND 90` | Drop |
| Price sanity | `properties` | `base_price BETWEEN 10 AND 10000` | Flag |
| Future dates | `bookings` | `check_in <= CURRENT_DATE + INTERVAL 365 DAYS` | Drop |

---

## 10. Reporting Cadence & Stakeholders

| Report | Frequency | Audience | Key Metrics |
| --- | --- | --- | --- |
| Executive Dashboard | Daily | Leadership | GBV, Net Revenue, Occupancy Rate, GSS |
| Host Performance | Weekly | Marketplace Ops | Superhost %, Response Time, Cancellation Rate |
| Support Operations | Daily | Support Team | Ticket Volume, Resolution Time, CSAT |
| Growth & Engagement | Weekly | Marketing | Conversion Rate, Bounce Rate, New Listings |
| Destination Insights | Monthly | Strategy | DPI, Seasonal Demand, RevPAN |

---

## Appendix A: Entity Relationships

```
users ─────┬─── bookings ─── booking_updates
            │         │
            │         ├─── reviews
            │         │
            │         └─── payments
            │
            └─── clickstream

hosts ───── properties ─┬─ property_amenities ─── amenities
                       ├─ property_images
                       └─ destinations ─── countries

customer_support_logs (standalone, joins to users via user_id)
page_views (standalone, joins to users via user_id)
employees (internal, standalone)
```

---

## Appendix B: Glossary

| Term | Definition |
| --- | --- |
| GBV | Gross Booking Value — total confirmed booking revenue before deductions |
| ADR | Average Daily Rate — revenue per booked night |
| RevPAN | Revenue Per Available Night — monetization efficiency |
| GSS | Guest Satisfaction Score — recency-weighted average rating |
| ALOS | Average Length of Stay — nights per booking |
| DPI | Destination Performance Index — composite destination ranking |
| CSAT | Customer Satisfaction — support resolution sentiment |
| Superhost | Host designation requiring ≥4.5 rating, ≥10 bookings/90d, <2% cancellations, ≥90% response rate |
| Booked Night | A single calendar night within a confirmed booking's check_in to check_out range |
| Active Listing | Property with a booking in trailing 90 days OR created within last 30 days |
