TABLE OF CONTENTS
1. Introduction
2. Installation for Development
	2.1 Prerequisites for Installation
	2.2 Installation
3. Installation for Server
	3.1 Prerequisites for Server
	3.2 Installation Steps


1. INTRODUCTION
Welcome to the installation instructions for Assignment Collector/Grader 
(ACG for short). In this file you will find directions on how to install
ACG on your computer for development and on a server for production.

It is *STRONGLY RECOMMENDED* that you read all of this document before
installing ACG.

The key difference between installation for development and production is
based on security. When Django makes a new project, it randomly generates
a secret key. For development, that is not necessary and you can copy our
project files with their existing (not secret anymore) key. But for 
production, you want a new project with a newly generated secret key.



2. INSTALLATION FOR DEVELOPMENT
You want this section if you want to contribute to or change ACG source
code. ACG is developed by a very small team (in fact, only one person!)
and we appreciate your contribution.


2.1 PREREQUISITES
There are a few things that have to be in place before you can start
developing ACG.
Assignment Collector/Grader needs:
	*	Python 2.x series, 2.6 or later.		  (http://www.python.org)
	*	Django 1.2 or later. 			   (http://www.djangoproject.com)
	*	JUnit 4.x or later						   (http://www.junit.org)
	
It is beyond the scope of this document to tell you how to install the
prerequisites, but Django and Python have excellent installation guides
available at their websites. 

For JUnit, you simply need the JAR file placed within your project folder
and then change a setting (explained below) to point to it.


2.2 INSTALLATION
By now, you should have Python and Django correctly installed on your
development system. The next step depends on how you get the source.

If you downloaded a zip/tarball from our project page,
http://sourceforge.net/projects/asgnmtgrader/
simply extract the contents of the archive to a folder on your system. 

However, we recommend that you get the latest source from our Mercurial
repository. We assume here that you have some experience working on a
collaborative project and are familiar with distributed source control.
To grab the latest source from our Mercurial repository, run:

hg clone http://hg.code.sf.net/p/asgnmtgrader/src assignmentcollectorgrader
hg update

This will create a directory called assignmentcollectorgrader in the 
directory you are currently in, put the repo inside, and get you a
working set. You *MUST* use the full name of the project for the folder
name. Otherwise, the development server will not work.

Open the settings.py file in the assignmentcollectorgrader directory, and
update the JUNIT_ROOT variable with the location and name of your JUnit
JAR file. For simplicity, we usually put it in a folder named JUnit under
the project folder.

In a shell, run:
python manage.py syncdb
to set up the database used for testing, and set you as an admin on the
built-in administration site.

To test your changes as you make them, run:
python manage.py runserver
and navigate in your web browser to localhost:8000
Note: Windows users may need to add a firewall exception.

For more information on developing with Django, refer to their tutorial
available in their web documentation.

To contribute your changes back to the project, talk to the developers.

Congratulations! You now have installed ACG for development. 
For any questions or comments, please go to our sourceforge site
and post in the forums.
Thank you.



3. INSTALLATION FOR SERVER
These instructions are for individuals who wish to use ACG in a class.
It is expected that you have basic system administration skills.


3.1 PREREQUISITES FOR SERVER
Before you can run ACG on your server, you need a few things:

	*	Python 2.x series, 2.6 or later.		  (http://www.python.org)
	*	Django 1.2 or later. 			   (http://www.djangoproject.com)
	*	JUnit 4.x or later						   (http://www.junit.org)
	*	An HTTP server with FastCGI or WSGI support.
	*	An SQL server (optional, see below)

It is beyond the scope of this document to explain how to properly set up
and install Python and Django, but their websites have excellent guides
already written on those subjects. Django also explains how to configure
your webserver of choice for hosting a Django app. Since we will not 
explain how to do that here, we refer you to that document as well.

You only need the JUnit JAR file, and to save it to the project directory
and change a setting (explained below), no installation required. Save it
someplace on your computer for now.

If you expect to serve many concurrent users, you will want to use an SQL
server like MySQL or PostgreSQL. The default of SQLite will do for a 
single class of about <40 students. To support multiple classes, a full
SQL server is recommended.


3.2 INSTALLATION STEPS
It is expected at this point that you have your webserver set up, and
have Python and Django correctly installed, and optionally, your SQL
server.

The easiest way to install ACG, which we recommend, is to download the
latest zip/tarball from our project site
http://sourceforge.net/projects/asgnmtgrader/

Then extract the archive to a folder NOT in your HTTP root.

We do not recommend using the latest source from our repository for your
production server. It may contain incomplete features, or bugs, and is 
not ready for production use.

Now you have to change a few settings specific to your installation.
Go into the assignmentcollectorgrader folder. Open settings.py in your 
favorite text editor.
	a)	Set DEBUG to False. Otherwise, in the event of an error in the
	code, users are greeted with a stack trace and lots of debug info
	that could be used to compromise the server.
	
	b) 	Set JUNIT_ROOT to the absolute path to the actual location of the
	JUnit JAR you downloaded earlier. For simplicity, we like to put it 
	into it's own folder under the project directory.
	
	c)	If you set up your own database server, you will need to change
	the databate settings under the DATABASES list. First, select the 
	database engine you are using, then the name of the database, and the
	other related settings relevant to your database configuration.
	
	d)	Update the MEDIA_ROOT and MEDIA_URL settings if you require a
	different configuration for those.
	
	e)	*IMPORTANT* Change the SECRET_KEY value to a new random value.
	It is very important that you DO NOT use the default value.
	
With the settings updated to the values specific to your installation,
now it is time to initialize the database for use.
Open a shell and naviagate to the project directory, then run:
python manage.py syncdb

This will initialize the database with the necessary tables for ACG and 
also prompt you for creating a superuser for site administration. If you
missed out on creating a superuser, you can edit the ADMINS section of
settings.py and add yourself there.

We now refer you to the Django documentation for deploying the project on
your server, available here
http://docs.djangoproject.com/en/1.3/howto/deployment/

If you have multiple Django sites on the same server, you may need to 
edit urls.py under the project folder to prevent URL collisions.