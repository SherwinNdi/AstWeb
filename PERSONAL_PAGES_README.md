# Personal Pages Implementation

## Overview
This implementation creates elegant, minimal personal pages for current team members (excluding Nadine Herzog, Jonathan Ray, Linda Grasser, Kathleen Wiencke, and all alumni).

## Design Principles
- **Golden Ratio Layout**: The main content area uses a 38.2% / 61.8% split (golden ratio)
- **Minimal & Elegant**: Clean design with proper spacing and typography
- **Researcher-Focused**: Optimized for academic profiles with publications and contact info
- **Interactive Publications**: Fixed-height scrollable box with year-based filtering

## Navigation Changes
**Personal pages are NOT in the menu bar.** Instead, they are accessed by clicking on team member photos/cards on the Team page ([/about/team](about/team.astro)).

- Each team member card links to their personal page (if eligible)
- Principal Investigator card also links to personal page
- Alumni continue to link to external webpages
- Excluded members link to their external webpage (if provided)

## Features

### 1. Page Structure
- **Top Section**: 
  - Profile photo (sticky on large screens)
  - Contact information card with icons
  - Download CV button (if CV URL is provided)
  - Name, title, and bio

### 2. Contact Links
Automatically displays available contact methods:
- Email (clickable mailto link)
- Phone (clickable tel link)
- Address
- ORCID
- University link
- Google Scholar
- GitHub
- OSF

### 3. Publications Section (New Interactive Design)
- **Fixed-height scrollable box** (600px height) for better space management
- **Year filtering**: Bottom bar with year buttons to filter publications
- **Show All button**: Reset filter to display all publications
- Automatically groups publications by type (Papers, Book Chapters, Posters, etc.)
- Smooth scroll to top when filtering
- Custom scrollbar styling
- Publications fade in/out with animation

#### How Year Filtering Works:
1. All available years are displayed as buttons at the bottom
2. Click a year to show only publications from that year
3. Active year button is highlighted
4. Click "Show All" to reset and see all publications
5. Container scrolls to top automatically when filtering

### 4. News & Updates
- Displays blog posts that mention the person
- Shows up to 6 most recent posts
- Includes publication date, title, and excerpt

## File Structure

```
src/
├── components/
│   ├── PersonalPage.astro          # Main personal page component (with year filter)
│   └── widgets/
│       └── TeamMembers.astro       # Updated to link to personal pages
├── pages/
│   └── personal/
│       └── [slug].astro            # Dynamic route for personal pages
├── data/
│   └── team.json                   # Extended with contact fields
└── navigation.ts                   # Personal menu removed
```

## Adding/Updating Member Information

To add or update member information, edit `/src/data/team.json`:

```json
{
  "name": "Member Name",
  "title": "Position Title",
  "image": "/team/image.png",
  "bio": "Short biography...",
  "email": "email@example.com",
  "phone": "+123456789",
  "address": "Office address",
  "orcid": "0000-0000-0000-0000",
  "universityLink": "https://university.edu/profile",
  "googleScholar": "https://scholar.google.com/...",
  "github": "https://github.com/username",
  "osf": "https://osf.io/profile",
  "cvUrl": "/path/to/cv.pdf",
  "publications": []
}
```

## URL Structure
Personal pages are accessible at: `/personal/member-name-slug`

Examples:
- Prof. Annette Horstmann: `/personal/prof-annette-horstmann`
- Arsene Kanyamibwa: `/personal/arsene-kanyamibwa`
- Manon Chédeville: `/personal/manon-chedeville`

## Navigation
A new "Personal" dropdown menu has been added to the main navigation, listing all eligible team members.

## Customization

### Golden Ratio Variables
The design uses CSS custom properties for golden ratio spacing:
```css
--golden-ratio: 1.618
--space-base: 1rem
--space-golden: calc(var(--space-base) * var(--golden-ratio))
--space-golden-2: calc(var(--space-golden) * var(--golden-ratio))
```

### Styling
The component uses Tailwind CSS classes and is fully responsive with:
- Mobile-first design
- Sticky sidebar on large screens
- Dark mode support

## Publication Matching
Publications are automatically matched using the author's last name. The system:
1. Extracts the last name from the member's full name
2. Searches for that name in the publication authors field (case-insensitive)
3. Displays all matching publications grouped by type

## Blog Post Matching
Blog posts are matched if the member's name appears in:
- Post title
- Post excerpt
- Post content

Limited to the 6 most recent matching posts.

## Testing
To test the personal pages:
1. Start the development server: `npm run dev`
2. Navigate to the Personal menu in the header
3. Click on any team member's name
4. Verify the page loads with correct information

## Future Enhancements
Consider adding:
- Manual publication selection per member
- Custom sections (Awards, Teaching, etc.)
- Social media integration
- Research interests tags
- Collaboration network visualization
