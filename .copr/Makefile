
srpm:
	dnf install -y rpmautospec rpm-build git
	rpmautospec process-distgit $(spec) $(spec)
	git archive -o ezaz-$$(rpmspec -q --queryformat='%{VERSION}\n' $(spec) | head -1).tar.gz HEAD
	rpmbuild -D "_sourcedir $$PWD" -D "_srcrpmdir $(outdir)" -bs $(spec)
