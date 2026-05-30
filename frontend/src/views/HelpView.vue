<template>
  <div class="help-view">
    <div class="container py-4">
      <h1 class="page-title">The Travelling Geographer</h1>

      <div class="help-content">
        <p>This application is meant to assist you, as a traveler, to organize the places in the world that you would like to travel to. It combines descriptions of destinations with maps, photos, links and searchable database attributes such as your assigned priority, a star rating, etc.</p>

        <h2>Overview — How It's Meant to Work</h2>
        <p>Travel destination ideas come to us many ways and our interest in any particular one grows until we actually have the opportunity to make the trip. Consequently, the status of any single destination progresses through the following list.</p>
        <ol>
          <li><strong>Suggested</strong> — Used for destinations that have been recommended by others that have caught your attention. Suggested implies that you have not yet decided if the destination is one that you desire to add to your Want-to-Visit list.</li>
          <li><strong>Want-to-Visit</strong> — Used once you decide that a destination is a place that you personally would want to visit, yet you have not done any serious research on costs, things to do, lodging, etc.</li>
          <li><strong>Researching</strong> — Used when you are generally ready to make a commitment to visiting the destination. You are now willing to invest time to get into the nitty-gritty of what a trip to the destination would entail.</li>
          <li><strong>Planned</strong> — Used when you have committed to travel and have dates selected. Switching to Planned as the status enables the journal feature so you can document your travel.</li>
          <li><strong>Visited</strong> — Used once you have returned from a destination. Journal entries remain available for adding and editing.</li>
          <li><strong>Archived</strong> — Used after the destination is no longer being actively pursued. This may be especially useful when you visited a destination a few years ago and want to start planning another trip to the same destination. Archived destinations can be shown or hidden from the Settings / General tab at any time.</li>
        </ol>

        <h3>The Overview Page</h3>
        <p>When you log in, you land on the Overview page. It provides a high-level snapshot of where things stand: status counts across the top, a world map showing all of your destinations, your most recently added destinations, and any upcoming trips with their travel dates. Clicking a status count filters the Destinations page to just that status. Clicking a destination takes you straight to its detail page.</p>

        <h2>Maps</h2>
        <p>After a number of destinations have been entered into the app, you will likely have numerous destinations that are reasonably close to one another. This is where the maps feature comes in. By using the map, you can visualize how multiple destinations relate to one another within a region. For example, you may have added destinations in Laos, Cambodia, and Vietnam not realizing they are only 50–100 km from one another across the borders. You can also filter destinations on the map based on fields from the database.</p>
        <p>Maps appear in several places throughout the app — the Overview page, the dedicated Map page, the destination detail page, and the destination edit form. Each map includes a layer control in the upper-right corner that lets you switch between a standard street map and a satellite imagery view. A scale indicator in the lower-left shows distance in either miles or kilometers depending on the unit preference in Settings.</p>

        <h2>Destinations</h2>
        <p>The Destinations page is your one-stop shop for viewing and filtering your destinations. In the grid view, each destination is presented on a card with a cover photo and information to quickly summarize the destination's status, priority, etc. In the list view, similar information is presented without a photo and in spreadsheet form. A select number of fields for multiple destinations can be edited in this view without needing to edit an individual destination.</p>

        <h3>Filtering</h3>
        <p>From the Destinations page, you are able to search, sort, and filter based on any of the fields in the database. This allows you to tease out information on which destinations deserve your attention. Note: The more information you enter for each destination, the better you can filter it later on.</p>

        <h3>Bulk Operations</h3>
        <p>In the grid view, click the Select button in the toolbar to enter selection mode. Each card displays a checkmark circle in the top-left corner of its image — click cards to select or deselect them. When one or more destinations are selected, an action bar appears at the bottom with three options:</p>
        <ul>
          <li><strong>Edit</strong> — Change the status, priority, or tags of all selected destinations at once. Each field is opt-in: enable a field to change it, leave it disabled to keep existing values. Tags can be added to existing tags or used to replace all existing tags.</li>
          <li><strong>Share</strong> — Share all selected destinations with another user at a chosen permission level.</li>
          <li><strong>Delete</strong> — Permanently delete all selected destinations along with their media, journal entries, and links.</li>
        </ul>
        <p>Use the "Select all" and "Deselect all" links in the action bar to quickly adjust your selection. Click Cancel in the toolbar to exit selection mode.</p>

        <h3>Adding a Destination</h3>
        <p>To add a new destination, click the "New Destination" button on the Destinations page. The form is organized into two columns. On the left you will enter the basic information — name, status, country, region, city, a rich-text description, and tags. Below that are the detail fields including priority, cost estimate, star rating, and best season to visit. Date fields appear based on status: planned travel dates when the status is Planned, and actual visit dates when the status is Visited. Any custom fields you have defined in Settings will also appear here.</p>
        <p>On the right side of the form is the location section. You can search for a place by name or click directly on the map to set coordinates. Once coordinates are set, the AI Populate button becomes available (see the Administration section for setup). The AI Populate button uses artificial intelligence to populate several fields of the destination and will warn you if any fields will be overwritten.</p>
        <p>At the bottom of the left column you can add links to relevant websites — hotel bookings, activity pages, travel blogs, etc. These links are saved with the destination and appear on its detail page.</p>

        <h3>The Destination Detail Page</h3>
        <p>Clicking on any destination opens its detail page, which is organized into tabs:</p>
        <ul>
          <li><strong>Overview</strong> — Shows the description, links, custom fields, a map of the location, a cover image (if available), and details summarizing the destination's attributes at a glance. Quick-access icons above the map let you search Google Images for the destination or open its coordinates in Google Maps.</li>
          <li><strong>Media</strong> — A photo gallery for the destination. You can upload files directly, or drag and drop (or paste) an image URL to download it from the web. Any image in the gallery can be set as the cover photo, which is the thumbnail shown throughout the app. Note: To drag and drop an image from Google Images, first click once on the image in Google Images, then drag the preview image to the drop area.</li>
          <li><strong>Journal</strong> — Available when the destination status is Planned, Visited, or Archived. This is where you document the trip itself — daily logs, highlights, reflections, whatever you like. Each entry has a date, title, optional star rating, and a rich-text body.</li>
        </ul>
        <p>From the detail page header, you can edit the destination, delete it, or share it with other users.</p>

        <h3>Sharing</h3>
        <p>If other users have accounts on your instance, you can share individual destinations with them. Click the Share button on the destination detail page, select a user, and choose a permission tier:</p>
        <ul>
          <li><strong>View</strong> — Read-only access.</li>
          <li><strong>Contribute</strong> — Can add media and journal entries.</li>
          <li><strong>Edit</strong> — Can modify the destination.</li>
          <li><strong>Manage</strong> — Full control including sharing and deletion.</li>
        </ul>
        <p>Shared destinations appear in the other user's destination list with the owner's name displayed. To view what you have shared or what others have shared with you, use the filters on the Destinations page.</p>

        <h2>Journal</h2>
        <p>The Journal page provides a unified, chronological timeline of all your journal entries across every destination. Rather than navigating destination by destination, you can scroll through your travel writing in one place.</p>
        <p>The filter bar across the top lets you search by keyword, filter by destination, or narrow to a date range. A sort toggle switches between newest-first and oldest-first ordering. Each entry shows the date, the destination it belongs to (which links back to that destination's detail page), the entry title, and the body text. Star ratings, if assigned, appear alongside the title.</p>

        <h2>Settings</h2>
        <p>The Settings page is organized into tabs.</p>

        <h3>General</h3>
        <p>Appearance and behavior preferences.</p>
        <ul>
          <li><strong>Dark Mode</strong> — Toggles the color theme.</li>
          <li><strong>Show Archived</strong> — Controls whether archived destinations appear in lists and on maps.</li>
          <li><strong>Show Notification Pop-ups</strong> — Controls whether success, info, and error messages appear as notifications in the upper right part of the application.</li>
          <li><strong>Metric Units</strong> — Switches the map scale between metric and imperial units.</li>
        </ul>

        <h3>Backup &amp; Restore / Export</h3>
        <p>Administrators see this tab labeled "Backup &amp; Restore" and have access to full backup and restore operations. The Backup button downloads a compressed archive containing all destination data and media files. A progress bar shows the status of the download. To restore, select a previously created backup file and click Restore — the app will rebuild the data and re-import all media. Non-administrators see this tab labeled "Export" with access to CSV export only.</p>
        <p>An Export CSV option is available to all users, allowing you to choose which fields to include and download a spreadsheet of your destinations.</p>

        <h3>Tags</h3>
        <p>A central place to view, rename, and delete the tags used across your destinations. Each tag shows how many destinations reference it. A search box lets you quickly find specific tags and a sort dropdown lets you order by count or alphabetically. Renaming a tag here updates it everywhere. Renaming a tag to the same name as another tag allows you to merge tags.</p>
        <p>Administrators have additional tools: select multiple tags using checkboxes and merge them into a single tag with the Merge button, or clean up unused tags with the Delete Unused button.</p>

        <h3>Custom Fields</h3>
        <p>If the built-in fields don't cover something you want to track, you can define custom fields here. Each field has a name and a type — either free text or a dropdown with predefined options. Once created, custom fields appear on every destination's edit form and detail page.</p>

        <h3>Bookmarklet</h3>
        <p>The Bookmarklet lets you quickly create a destination while browsing the web. To setup, simply drag the provided bookmarklet link (button) to your browser's bookmarks bar. When you are on another website and want to save it as a destination, click the bookmarklet link — it will clip the page's title, URL, and description into a new destination in the app.</p>

        <h2>About</h2>
        <p>The About dialog is accessed from the user menu in the upper-right corner of the navigation bar. It displays the application name, current version number, build date, and copyright and license information.</p>

        <h2>Logout</h2>
        <p>Also found in the user menu, Logout ends your session and returns you to the login screen. Your data remains safely stored on the server and will be right where you left it next time you log in.</p>

        <h2>Administration</h2>
        <p>The administration functions are only visible to users who have been assigned the Administrator role. If you don't see these options, it is because you do not hold the Administrator role.</p>

        <h3>User Management</h3>
        <p>Accessible from the user profile menu, the Users page is where administrators create and manage user accounts. The table shows each user's name, email, account type (Administrator or User), status (Active or Disabled), and last login date.</p>
        <p>When adding a user, checkboxes control whether the account is an Administrator, Active, and Approved (to be implemented later). Editing a user follows the same form — leaving the password field blank keeps the existing password. You cannot delete your own account.</p>
        <p>When deleting a user who owns destinations, you are given the choice to either transfer all of their destinations to another user or permanently delete them along with their media and journal entries. Transferring preserves all data under the new owner, while deleting removes everything permanently.</p>

        <h3>AI Configuration</h3>
        <p>The AI tab in Settings allows you to configure AI-powered destination population using Google Gemini. An Administrator must configure an API key, which is not visible to non-Administrators, prior to use. To set it up:</p>
        <ol>
          <li>Obtain a free API key from <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer">Google AI Studio</a>.</li>
          <li>Enter the key in the Settings / AI tab and click Save Key.</li>
          <li>Use the Test Connection button to verify it works.</li>
        </ol>
        <p>Once configured, an AI Populate button appears on the destination edit form whenever coordinates are set. Clicking it sends the location to Gemini, which returns a description, country, region, best seasons, and other details. If fields already contain data, you are given the choice to overwrite existing values or only fill empty fields.</p>
        <p>The prompt template used for AI requests is fully customizable from the same tab. You can modify it to tailor the kind of information Gemini returns, or reset it to the default at any time. A model dropdown lets you choose which Gemini model to use — different models offer trade-offs between speed and detail, so experiment to find what works best for your needs.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.help-view {
  min-height: 100vh;
  background: var(--color-bg);
  padding-bottom: 4rem;
}

.page-title {
  margin: 0 0 2rem 0;
  font-size: 2.25rem;
  color: var(--color-text-bright);
}

.help-content {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 0.5rem;
  padding: 2rem 2.5rem;
  color: var(--color-text);
  line-height: 1.7;
}

.help-content h2 {
  color: var(--color-text-bright);
  font-size: 1.5rem;
  margin: 2.5rem 0 0.75rem 0;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--color-border);
}

.help-content h2:first-of-type {
  margin-top: 1.5rem;
}

.help-content h3 {
  color: var(--color-text-bright);
  font-size: 1.15rem;
  margin: 1.75rem 0 0.5rem 0;
}

.help-content p {
  margin: 0.6rem 0;
}

.help-content ol,
.help-content ul {
  margin: 0.6rem 0 0.6rem 1.5rem;
  padding: 0;
}

.help-content li {
  margin: 0.4rem 0;
}

.help-content strong {
  color: var(--color-text-bright);
}

.help-content a {
  color: var(--color-accent-hover);
  text-decoration: none;
}

.help-content a:hover {
  text-decoration: underline;
}

.py-4 {
  padding-top: 1.5rem;
  padding-bottom: 1.5rem;
}

@media (max-width: 768px) {
  .help-content {
    padding: 1.25rem 1rem;
  }
}
</style>
