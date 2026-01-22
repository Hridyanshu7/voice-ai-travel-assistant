# Initial User Prompt for generating PRD

Should the itinerary editing flow introduce explicit “lock” controls so users can mark certain POIs/blocks as “don’t change” before edits?
Sure, if it doesn't take too much of effort in development.

How aggressively should the system simplify language in explanations for non-technical travelers versus preserving detailed reasoning?
Moderately aggressive, need to make sure 75% of travel enthusiasts are satisfied with the language output and find it familiar.

What is the minimum viable city and dataset coverage for the first public demo (e.g., 1–2 cities with rich data vs. generic support for many cities with thinner data)?
Cover the following cities specifically:
All Metros in India \& all capital cities of India's neighboring countries well enough

How should the system handle time zone and public holiday differences that affect opening hours and feasibility?
Definitely to be handled for any destination chosen basis info available about the specific landmarks, accommodations \& destinations

Should there be a simple history/versions view to compare “before” and “after” itineraries when testing edit correctness?
Nope, not needed at all.

Here is the updated PRD with your answers to the open questions incorporated.

***

# Voice-First AI Travel Planning Assistant

`/tasks/prd-voice-first-travel-planner.md`

## 1. Introduction / Overview

This feature is a **voice-first** AI travel planning assistant that helps users turn their preferences, time constraints, and travel conditions into a realistic, day-wise itinerary for one or more cities over 2–4 days (or as specified by the user). The assistant supports spoken trip requests, generates grounded itineraries, allows voice-based edits, and explains its decisions in a way that a non-expert traveler can understand.[^1][^2]

The goal is to build a deployed prototype that demonstrates end-to-end capability: voice input, grounded trip planning using public datasets and MCP tools, voice-based itinerary editing, explanation of choices, AI evaluations, and PDF export + email delivery without relying on n8n.[^3][^4]

***

## 2. Goals

- Provide a **voice-first trip planner** where users can describe a trip in natural speech and receive a feasible, day-wise itinerary.
- Ensure all recommendations (POIs, routes, tips) are **grounded** in public data, with clear citations shown in the UI.[^1][^3]
- Support **voice-based edits** that modify only the relevant parts of the itinerary while preserving the rest.
- Deliver clear, user-facing **explanations** for why each place and schedule decision was chosen, using moderately simplified language that feels familiar to at least 75% of travel enthusiasts.
- Implement at least **three evaluation checks**: feasibility, edit correctness, and grounding/hallucination detection, which can be run on demand.[^2][^5]
- Generate a **PDF itinerary** and email it to the user through the application architecture (custom workflow), not via n8n.

***

## 3. User Stories

### 3.1 Voice-based trip planning

- As a traveler, I want to **speak my trip request** (e.g., “Plan a 3-day trip to Jaipur next weekend. I like food and culture, relaxed pace.”) so that I don’t have to fill long forms.[^6][^7]
- As a traveler, I want the assistant to **ask only essential follow-up questions** (e.g., dates, budget level, must-visit places) so planning stays conversational and not overwhelming.[^8][^9]
- As a traveler, I want to **confirm key constraints** (dates, city/cities, pace, budget, number of travelers) before the itinerary is generated, so the plan reflects my real constraints.


### 3.2 Itinerary viewing and structure

- As a traveler, I want to see a **day-wise itinerary** broken into **Morning / Afternoon / Evening** blocks so I can quickly understand the trip flow.[^10][^11]
- As a traveler, I want each item to show **duration and approximate travel time between stops**, so I can judge whether the plan looks realistic.[^5][^12]
- As a traveler, I want a **“Sources” or “References” section** that shows where information about POIs and tips came from (e.g., OSM, Wikivoyage, TripAdvisor), so I trust the recommendations.[^3][^1]


### 3.3 Voice-based editing

- As a traveler, I want to **edit the itinerary using voice** (e.g., “Make Day 2 more relaxed”, “Swap the Day 1 evening plan to something indoors”, “Add one famous local food place”), so I can refine the plan quickly.[^13][^8]
- As a traveler, when I request an edit, I want **only the relevant part** of the itinerary (e.g., Day 2 afternoon) to change, and all other days/blocks to remain as they were.
- As a traveler, I want to be able to **lock certain POIs or blocks** as “don’t change” before requesting edits, so that my must-keep items are preserved with minimal additional effort from me.
- As a traveler, I want to be able to **undo or adjust an edit** (e.g., “Actually keep the museum from before”) so I am not stuck with unwanted changes.


### 3.4 Explanations and reasoning

- As a traveler, I want to ask **“Why did you pick this place?”** and get a short, clear explanation based on real info (e.g., historical importance, reviews, suitability for my interests) with citations.[^14][^1]
- As a traveler, I want to ask **“Is this plan doable?”** and get a reasoned answer that references daily time, travel time, opening hours, and public holidays in the destination.
- As a traveler, I want to ask **“What if it rains?”** and receive adjusted suggestions or clear guidance on how the itinerary would change (e.g., swap outdoor activities to indoor ones).


### 3.5 Export and email

- As a traveler, I want to **receive a PDF** version of my final itinerary via email so I can access it offline and share it easily.[^15][^10]
- As a traveler, I want the **PDF** to include days, time blocks, POI details, and brief tips so it is usable during the trip.

***

## 4. Functional Requirements

### 4.1 Voice input and transcription

1. The system must accept **spoken input** from the user using a microphone button in the UI.
2. The system must use a **third-party STT (speech-to-text) API** (e.g., Deepgram, Whisper, or equivalent) to transcribe the audio into text.[^16][^17]
3. The UI must display a **live transcript** of what the system hears, so users can see and correct misunderstandings.
4. The system must handle **multi-turn conversations**, preserving context across turns (e.g., follow-up voice questions, clarifications, edits).[^13][^8]

### 4.2 Intent understanding and trip preference collection

5. The system must extract key constraints from user input, including: city/cities, dates or relative time (e.g., “next weekend”), number of days, interests (food, culture, nightlife, nature), pace (relaxed/standard/packed), and any must-visit POIs.[^2][^1]
6. The system must **ask at most 6 clarifying questions** when needed (e.g., missing dates, unclear city name, missing pace preference).
7. The system must present a concise **constraint summary** back to the user (spoken + shown as text) and request confirmation before generating the itinerary.

### 4.3 MCP-based data access and itinerary generation

8. The orchestration layer must use at least **two MCP tools**:
    - `poi_search` from **Travel Data MCP**.
    - `build_itinerary` from **Itinerary MCP**.[^4][^3]
9. The **Travel Data MCP** must expose:
    - Tool `poi_search`: Inputs include city/cities, user interests, constraints (e.g., avoid long walks, kid-friendly), and date range; outputs include ranked POIs with metadata (name, category, geo-coordinates, approximate duration, opening hours, source dataset IDs, and source URLs).[^4][^3]
    - Tool `estimate_travel_time` (optional but recommended): Inputs include ordered POI locations and transport assumptions; outputs include estimated travel times between stops.[^12][^5]
10. The **Itinerary MCP** must expose:
    - Tool `build_itinerary`: Inputs include candidate POIs from `poi_search`, user constraints (days, daily time window, pace, must/avoid, budget hints), and optionally `estimate_travel_time` outputs; outputs include a structured, day-wise itinerary with time blocks, assigned POIs, and expected durations and travel times.[^5][^2]
    - Tool `adjust_itinerary_for_weather` (optional): Inputs include existing itinerary, location, date range, and forecast data; outputs include adjusted itineraries that account for predicted weather (e.g., moving outdoor activities away from rain periods).[^18][^5]
11. The system must ensure that POIs used in the itinerary can be **mapped back to dataset records** (e.g., OSM IDs, TripAdvisor IDs, Wikivoyage pages) for grounding and citations.[^1][^3]

### 4.4 RAG-based travel guidance and explanations

12. The system must use **RAG (Retrieval-Augmented Generation)** to fetch travel tips and context from publicly available sources (e.g., Wikivoyage, Wikipedia, curated travel blogs, forums, and travel booking sites where allowed).[^3][^1]
13. The RAG layer must support retrieval for:
    - City-level guidance (areas to visit/avoid, typical routes, safety, etiquette, seasons).
    - POI-level context (short descriptions, best time to visit, booking requirements).
14. All **factual travel tips** surfaced to the user must have at least one **citation** pointing to the underlying source.
15. When information is missing or uncertain (e.g., no clear data on opening hours or holiday exceptions), the system must **explicitly state this** rather than inventing details.[^12][^1]
16. Explanations produced by the system must use **moderately simplified, traveler-friendly language**, aiming for familiarity and clarity for at least 75% of travel enthusiasts (e.g., avoid heavy technical jargon and overly formal phrasing).

### 4.5 Geographic and dataset coverage

17. For the initial public demo, the system must **specifically support**:
    - All metro cities in India (e.g., Delhi NCR, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, etc.).
    - Capital cities of India’s neighboring countries (e.g., Kathmandu, Colombo, Dhaka, Islamabad, Thimphu, etc.), assuming sufficient public data is available.[^19][^20]
18. For these cities, the POI and RAG datasets must be “reasonably complete” for typical tourist interests (food, culture, heritage, markets, major attractions), using OSM/Overpass plus supported travel sites and guides where feasible.[^1][^3]

### 4.6 Time zones, opening hours, and public holidays

19. The system must handle **time zones** for any supported destination, ensuring that daily time windows and event times are interpreted in the destination’s local time.
20. The system must consider **opening hours** and, where data is available, **public holidays or special closures** that affect attractions, accommodations, and key destinations.[^12][^1]
21. When holiday or closure information is unavailable, the system must:
    - Surface this uncertainty explicitly.
    - Avoid making hard guarantees (e.g., “definitely open”) based on guesswork.

### 4.7 Itinerary display and companion UI

22. The UI must show a **day-wise itinerary view** (Day 1 / Day 2 / Day 3 / …) with each day broken into Morning, Afternoon, and Evening blocks.[^11][^10]
23. Each block must display: POI name, short description, planned duration, and **estimated travel time** from the previous block.
24. The UI must include a **microphone button** for starting/stopping voice capture and a live transcription area.
25. The UI must include a **“Sources” or “References” section** listing all external sources used for POIs and tips (e.g., OSM, Wikivoyage, TripAdvisor), with links where possible.[^3][^1]
26. The UI may highlight updated blocks after edits, but a full history/versions comparison view is **explicitly out of scope**.

### 4.8 Voice-based editing and locking

27. The system must accept voice commands that request edits to the itinerary (e.g., “Make Day 2 more relaxed”, “Reduce travel time overall”, “Add a famous local food place on Day 1 evening”).[^8][^13]
28. The intent-handling layer must resolve:
    - Target scope (trip-wide vs. specific day vs. specific block).
    - Type of change (relaxation, swap, add, remove, replace, time compression).
29. The system must allow users to **lock specific POIs or blocks** as “don’t change” via a simple interaction (e.g., checkbox or icon tap) before applying edits, subject to reasonable development effort.
30. When an edit is applied, the system must ensure that **only the affected sections** of the itinerary change and that locked items and other days/blocks remain stable wherever feasible.
31. The system must allow users to **confirm or reject** the updated itinerary after an edit.

### 4.9 Explanations and “why” questions

32. The system must support user questions like:
    - “Why did you pick this place?”
    - “Is this plan doable?”
    - “What if it rains?”
33. For “why” questions, the system must generate explanations referencing:
    - User preferences (interests, pace, constraints).
    - POI attributes (category, popularity, relevance).
    - Practical considerations (distance, time zones, opening hours, public holidays, weather when available).[^5][^1]
34. Explanations must reference **real data from MCP outputs and RAG**, and must show citations or references in the UI.
35. Explanation text must remain **concise and moderately simplified**, avoiding deep technical detail unless explicitly requested by the user.

### 4.10 PDF generation and email delivery

36. The backend must generate a **PDF itinerary** from the final agreed itinerary structure, including: trip summary, day-wise schedule, POIs, durations, and essential tips.[^15][^10]
37. PDF generation must be implemented **inside the app architecture** (e.g., HTML-to-PDF library in the backend), not via n8n.
38. The backend must send the PDF to the user’s email using an **email delivery mechanism** (SMTP or transactional email API) with appropriate error handling and success/failure notification in the UI.

### 4.11 AI evaluations

39. The system must implement a **Feasibility Eval** that checks:
    - Total planned time per day does not exceed available daily time by a configurable margin.
    - Travel times between POIs are reasonable given city and distance.
    - Pacing is consistent with user preference (relaxed vs. packed).[^2][^5]
40. The system must implement an **Edit Correctness Eval** that verifies:
    - Edits change only the intended day/blocks according to the requested scope.
    - Locked POIs/blocks remain unchanged.
    - The rest of the itinerary matches the prior version (structurally and in content) where untouched.
41. The system must implement a **Grounding \& Hallucination Eval** that ensures:
    - All POIs correspond to real dataset records from the MCP data sources.
    - All tips and explanations referencing external facts have an associated citation.
    - Uncertainty or missing data is clearly surfaced (no fabricated specifics).[^1][^3]
42. Evaluations must be **runnable** (e.g., via backend endpoints or scripts) and should produce machine-readable results that can be logged or displayed in a simple debug view (not necessarily visible to end users).

***

## 5. Non-Goals (Out of Scope)

- Supporting **arbitrary-length trips** beyond what is feasible for the capstone (e.g., 3+ weeks, many cities) is out of scope; the focus is on short trips (2–4 days) and a small number of cities per trip.[^2][^1]
- Real-time integration with airline, train, or bus booking APIs is out of scope; travel time may be heuristic.
- Complex group trip coordination features (multiple travelers with conflicting preferences, voting, shared editing) are out of scope.[^18][^13]
- Full mobile-native apps (iOS/Android) are out of scope; the primary interface is a web-based UI.
- Detailed legal or compliance modules (e.g., insurance, visa rules) are out of scope; only high-level generic advice may be given if sourced and cited.
- A **version history or detailed before/after comparison UI** for itineraries is explicitly out of scope.

***

## 6. Design Considerations

- The UI should prioritize **voice interaction** visually (microphone prominent, transcript always visible) while still supporting text input as a fallback.[^9][^16]
- Itinerary layout should be **simple and scannable**, with clear separation between days and between Morning/Afternoon/Evening.[^10][^11]
- Explanations and citations should be **concise** in the main view, with expandable sections or modals for deeper source details.
- A simple locking affordance (e.g., a small “lock” icon on each POI/block) should be provided where feasible, without significantly increasing development complexity.
- Error states (e.g., STT failures, MCP tool timeouts, missing data) should be clearly communicated with actionable options (retry, adjust constraints, switch to text input).[^17][^9]

***

## 7. Technical Considerations

- **Frontend**: Web app with microphone access, using browser APIs for audio capture; STT via third-party API; TTS is optional but recommended for better voice UX.[^16][^9]
- **Backend**:
    - Handles orchestration between STT results, LLM calls, MCP tool calls, RAG retrieval, evaluations, and PDF/email workflows.
    - Must maintain session context for multi-turn conversations.
- **MCP Integration**:
    - Travel Data MCP and Itinerary MCP implemented as separate MCP servers or as logically separated services behind a single MCP endpoint.[^4][^3]
    - Ensure tools have well-defined JSON schemas for input/output.
- **RAG Stack**:
    - Use a vector database or equivalent index to store city and POI guidance from Wikivoyage, Wikipedia, curated blogs, forums, and travel sites where allowed.[^3][^1]
    - Ensure that content usage respects source terms where applicable.
- **Time and Holidays**:
    - Use timezone libraries and, where possible, public holiday APIs or datasets for major countries to adjust feasibility and explanations.
- **PDF \& Email**:
    - Use a reliable server-side PDF generator (e.g., headless browser or HTML-to-PDF library) and a standard email provider for sending itineraries.[^15][^10]
- **Logging \& Observability**:
    - Log MCP calls, evaluation results, and key user interactions (anonymized) for debugging and demonstration.[^4][^3]

***

## 8. Success Metrics

- **Voice UX \& Intent Handling**
    - ≥ 80% of demo test trips result in a correct interpretation of city, dates, and core preferences on first attempt (or within allowed clarifications).[^13][^2]
- **Language Familiarity**
    - At least 75% of test users who self-identify as travel enthusiasts rate explanation language as “clear” or “very clear” and “familiar” rather than “too technical” or “too simplistic”.
- **Itinerary Quality \& Feasibility**
    - ≥ 80% of evaluated itineraries pass the Feasibility Eval without critical issues.[^5][^2]
- **Edit Correctness**
    - ≥ 80% of evaluated edits modify only intended sections and preserve locked blocks according to the Edit Correctness Eval.
- **Grounding \& Citations**
    - ≥ 95% of POIs used in itineraries have valid dataset IDs.
    - ≥ 90% of factual tips in the UI have at least one citation.[^1][^3]

***

## 9. Open Questions

- None at this time; earlier open questions have been resolved into explicit requirements and design decisions.
<span style="display:none">[^21][^22][^23][^24][^25][^26][^27][^28][^29][^30]</span>
