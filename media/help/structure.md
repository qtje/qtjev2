# Comic Structure

This document provides a technically-themed description of the structure of qtjev2 as it compares to conventional web comics.

## Conventional Web comics

A conventional web comic has a familiar structure: it consists of a sequence of pages each of which provides a link to the previous page and the next page. Often there will also be links to the first and last pages of the comic. It's fairly straightforward to represent a conventional web comic as a doubly-linked list, but it's also possible to represent it as a graph with a specific set of constraints.

### As an unweighted directed graph

For the purposes of this document, a graph consists of **nodes** connected by **edges** that **originate** at a node (the **origin**) and **terminate** at a node (the **terminus**). In a web comic, the nodes of the graph are pages of the comic, and the edges are links between pages. Each page renders the links it originates as links for navigation, and so each link has a type. Typically the link types are "first," which takes the user to the first page of the comic, "previous," which takes the user to the previous page, "next," which takes the user to the next page, and "last" or "current," which takes the user to the final page. There are constraints on the kinds of link a page can originate, and these constraints divide pages into three categories:

#### First Page

* There may only be one page of this type
* With the exception of a "first" link, the page may not link to itself
* The page is the origin of one "next" link
* The page is the terminus of exactly one "previous" link
* The page is the terminus of a "first" link from every other page in the comic
* The page originates a single "last" link

#### Last Page

* There may only be one page of this type
* With the exception of a "last" link, the page may not link to itself
* The page is the origin of one "previous" link
* The page is the terminus of exactly one "next" link
* The page is the terminus of a "last" link from every other page in the comic
* The page originates a single "first" link

#### Middle Page

* There may be any number of pages of type
* The page may not link to itself
* The page is the origin of one "next" link
* The page is the terminus of exactly one "previous" link
* The page is the origin of one "previous" link
* The page is the terminus of exactly one "next" link
* The page originates a single "first" link
* The page originates a single "last" link

### Visual representation

![Page form mapping]({% static 'help/conventional_graph.svg' %})


## qtjev2

Like a conventional web comic, qtjev2 may be represented using an unweighted directed graph, but the constraints on the structure of the graph are different. In qtje, there is no "last" link, and there is only one type of page, and it is subject to the following constraints:

* Every page originates a "first" link to page 0000
* Every page and every link has an owner
* A page may have at most three "next" links and "three" previous links
* A page may have at most two "next" links that belong to its owner
* A page may have at most two "next" links that do not belong to its owner
* A page may have at most two "previous" links that belong to its owner
* A page may have at most two "previous" links that do not belong to its owner

The "first" page of qtje serves as a landing page for a reader to begin the comic and has no other special significance. As is often the case with conventional web comics, the "first" link doesn't have an explicit representation, but generated dynamically for each page according to the defined "first" page of the comic. At one point the database supported "first" type links, but the concept added excessive overhead, and I didn't expect it would be used frequently or provide much value. This could conceivably change at some point in the future, though.

In a conventional web comic, the first and last pages can both be identified procedurally thanks to their uniqueness. Ignoring "last" links, it is possible for a qtjev2 to fall into one of the conventional web comic page types, and it is therefore possible to construct a convention web comic within qtjev2. 

Since the only terminus page for "first" links is page 0000, there can only be a single first page, and that page must be page 0000. If at some future time page 0000 acquires 1 or more "previous" links or more than 1 "next" link, it will cease to fit the definition of a first page. Therefore, qtjev2 may have either 0 or 1 first page.

Due to the exclusion of "last" links, the definition of a last page in the context of qtjev2 is simple a page originating exactly one "previous" and one "first" link while terminating one "next" link. Nothing in qtjev2 constrains the number of pages that can meet this definition. Since the last page of qtje is not unique, it is not possible to procedural determine the unique final page, and so qtjev2 has no concept of a "last" link. While "last" links could in principle be specified manually, a common characterstic of last pages in conventional web comics is that they change over time, and it is typically desirable for the "last" links to always point at the unique last page. This is not likely to be possible in qtjev2 since multiple authors will likely own multiple last pages. In addition, the exclusion of the "last" link creates a pleasing symmetry for the navigation links and evokes both the uniusual topology of qtjev2 and the final state of qtje.

### Visual representation

A more intuitive definition for a first or last page may simply be a page having no "previous" link or no "next" link respectively. In the below diagram, pages matching the relaxed definition for first page have a thick solid border, and pages matching the relaxed definition of a last page have a dashed border. For clarify, the "first" links are drawn only at their origins and termini.

Note that there may be multiple first and last pages. The present implementation of the "first" link guarantees at least one trivial path between any two pages, but unlike a contentional webcomic, there may not be a path between any two pages that does not contain a "first" link.

![Page form mapping]({% static 'help/qtjev2_graph.svg' %})

## History as narrative structure

A conventional web comic typically has a trivial history. It starts out as a single page, and then new pages are added one at a time, each becoming the new last page. qtjev2's less-constrained structure permits non-trivial histories as pages can be added with links to and from almost any other page in the comic (and not just the last page). In addition while the links in a conventional web comic change only under exceptional circumstances (such as a page being removed), the links in qtjev2 may change at any time as long as they satisfy the comic's structural constraints. Therefore the history of qtjev2 cannot be procedurally generated with high accuracy. Instead, the history is maintained explicitely in database.

It is possible to access qtjev2 as it was at any point in the past using a a querystring e.g. [https://qtje2.com/0007?date=2022-09-20-16:20](https://qtje2.com/0007?date=2022-09-20-16:20). The date is in UTC and is may be any format recognized by `dateutil.parser`. At present there is no UI for simplified revision inspection or navigation.

Since the structure of the comic can change substantially over time, the history provides an additional axis for the creation of narrative structure. For example, by replacing links a sequence of pages can be subsituted for a different sequence of pages, new pages may be inserted, or existing pages may be made inaccessible (though not deleted).

### Implementation

Pages, aliases, story arcs, templates, and themes all have a creation date and a special key called a history key. When one of these objects is modified, a new copy is created with the same history key as the old copy, a new creation date, and the desired modifications. There is no mechanism for identifying a deleted object, and so these objects can only be deleted by manually removing all of their versions from the database. The current version of any given object at any given time is simply the version having the most recent creation date that isn't later than the target time.

Links are a special case. Since links are defined solely by the pages they relate, links can be thought of a static objects that either exist or do not exist rather than persistent objects that change over time like pages. A change to a link can be modelled equivalently as simultaneous deletion of one link and creation of another. In order to simplify implementation, links don't have a history key and instead have both a creation date and a deletion date.

