
srpm:
	dnf install -y rpmautospec rpm-build git
	git archive -o ezaz-$(rpmspec -q --queryformat='%{VERSION}\n' $(spec) | head -1).tar.gz HEAD
	rpmautospec process-distgit $(spec) $(spec)
	rpmbuild -D "_sourcedir $PWD" -D "_srcrpmdir $(outdir)" -bs $(spec)
