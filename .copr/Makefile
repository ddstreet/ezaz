
EZAZ_VERSION:=$(shell rpmspec -q --queryformat='%{VERSION}\n' $(spec) 2>/dev/null | head -1)

srpm:
	dnf install -y rpmautospec rpm-build git
	git archive --prefix=ezaz-$(EZAZ_VERSION)/ -o ezaz-$(EZAZ_VERSION).tar.gz HEAD
	rpmautospec process-distgit $(spec) $(spec)
	rpmbuild -D "_sourcedir $$PWD" -D "_srcrpmdir $(outdir)" -bs $(spec)
