# qtjev2 Author Quickstart Guide

## What is qtjev2?

In simplest terms, qtjev2 is a system that faciliates multi-user construction of a directed graph for the purpose of imposing narrative structure on a collection of comic pages. This short tutorial will cover the basic steps required to implement a conventional linear webcomic structure in qtjev2.

## Content Guidelines

Please do not post anything illegal. All content posted to the site must be CC0 or equivalent (i.e. public domain). Otherwise, do what you want.

## Create an Alias

All qtjev2 Pages and Links are owned by an Alias owned by and Author. Therefore you'll need to create an Alias to begin posting. You can click the `ALIASES` link at the top of the page to manage your Aliases. This page lists all of your Aliases (none until you create one). Click `New Alias` to create a new Alias.
![Alias Management Page]({% static 'help/alias_mgmt.png' %})

You'll be presented with a form to create a new alias

![Alias Creation Form]({% static 'help/alias_form.png' %})

The Display Name the name that will be used to identify the Alias that created a page or link. After creation, and alias's display name can be changed at any time by clicking the `Edit` link on the `ALIASES` page.

Enter a suitable display name and click `Create Alias` to create your Alias.

## Upload a page

### Access the Page upload form

Click the `PAGES` link at the top of the page to manage your Pages. This page will list all pages you have posted. To upload a new page, click `New Page`.

![Page management page]({% static 'help/page_mgmt.png' %})

You'll be presented with a form to upload a new Page.

![Page upload form]({% static 'help/page_form.png' %})

### Simple page upload

The form comes populated with one of your Aliases, but the Alias can be changed by typing the display name of an alias into the Alias field and then selecting the matching Alias from the dropdown.

The minimum required to upload a new page is an image (selected via the Browse button in the Image field), but you'll typically also want to link to a previous page. You can type the number of title of the previous page in the Previous Page field and select the matching page from the dropdown. If you haven't created any pages, then you'll have to link to a page created by another author. You can link to a page that already has a next page as long as it has fewer than 3 next pages.

At this point, you could click `Create Page` to upload the new image as a comic page following the selected previous page and published as the selected Alias. Along with alt text, this is all you need to create a conventional serial webcomic. Note that once created, pages can be edited but cannot be deleted. This is true of all comic objects except links between pages.

### Field Mapping

The image below shows how the fields in the form map to the displayed page using the default template and theme, qtje modern.

![Page form mapping]({% static 'help/page_form_map.png' %})

### Previous Page and Page Linking

By default, the Reciprotate box next to Previous Page is checked. Links between pages are one-way, and the Reciprocate option has the effect of ensuring the the selected Previous Page also link to the new page as its next page.

When the Reciprocate option is selected, two links will be created with the page. One will be a previous link assigned to the new page pointing at the previous page, and the other will be a next link assigned to the previous page and pointing at the new page. If it is not possible to create both links, then the page upload will fail with an error messsage.

![Link creation]({% static 'help/link_recip.png' %})

Each page can have 3 next links and 3 previous links. One of each is reserved for the Alias that owns the page, one of each is reserved for an Alias that does not own the page, and the final pair can be created by anyone.

Though it would make your page difficult to find, it is possible to create a page that doesn't have a previous page link by default. To do this, leave the Previous Page field blank and uncheck the Reciprocate checkbox.


### Story Arcs

Story arcs are objects used to group pages, typically indicating that a page belongs to a specific narrative arc. In this comic, Story Arcs are objects owned by an alias that include a display name that is used to represent the arc. The Story Arc owner can change the display name of the arc at any time, and any Page can include itself any Story Arc even if the Page owner isn't the Story Arc owner.

A default Story Arc called "No Story" is provided for uncategorized pages.

### Themes and Templates

A Theme is a collection of django template snippets that defines the rendering of the navigation bars above and below the comic. A Template is a django snippet that defines the rendering of the comic image.

Themes and Templates belong to Aliases, but can be used by any Alias.

## Additional Content Guidelines

I won't well you want to do, but I'm pretty sure Kant says I have to tell you what I'm going to do:

* Upgrading from yellow to green
* Wandering the Time Ocean forever
* Encountering the King of Time
    * Repeatedly
* Trying to find a way to reach 2021
* No more asphalt
