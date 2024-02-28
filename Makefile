main:
	@python proc/process.py NAPR.pnml NAPR.nml
	@nmlc -c --grf NAPR.grf NAPR.nml
