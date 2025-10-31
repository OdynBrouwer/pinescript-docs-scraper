"""Orchestrator to run the scraper and processor scripts in this repo.

This script loads `1_scrap_docs.py` and `2_process_docs.py` by file path
and invokes their main behaviors directly. We use importlib to load the
files because `1_scrap_docs.py` starts with a digit and therefore can't be
imported with a plain module name.

Usage:
	python 3_scrap_and_process.py        # run crawl then process
	python 3_scrap_and_process.py --crawl-only
	python 3_scrap_and_process.py --process-only

This file intentionally avoids executing the crawler during import; it
explicitly calls the crawler's async main or run method when requested.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib.util
import os
import sys
from pathlib import Path


def load_module_from_path(name: str, path: str):
	"""Load a module from a filesystem path and return it.

	name: synthetic module name to register in sys.modules
	path: absolute or relative path to the .py file
	"""
	spec = importlib.util.spec_from_file_location(name, path)
	if spec is None or spec.loader is None:
		raise ImportError(f"Cannot load module from {path}")
	module = importlib.util.module_from_spec(spec)
	# Register in sys.modules so relative imports inside modules behave
	sys.modules[name] = module
	spec.loader.exec_module(module)
	return module


async def run_crawler_module(mod, *, verbose: bool = True):
	"""Run the crawler module. Accepts either an async `main()` function
	or a `PineScriptDocsCrawler` class that exposes `run()` or `main()`.
	"""
	if hasattr(mod, "main"):
		main_obj = getattr(mod, "main")
		if asyncio.iscoroutinefunction(main_obj):
			if verbose:
				print("Running crawler: async main() from module")
			await main_obj()
			return

	# Fallback: instantiate the crawler class and call its async run()
	if hasattr(mod, "PineScriptDocsCrawler"):
		if verbose:
			print("Running crawler: PineScriptDocsCrawler.run()")
		crawler_cls = getattr(mod, "PineScriptDocsCrawler")
		crawler = crawler_cls()
		# prefer async run() if present, else call sync run() if available
		if hasattr(crawler, "run"):
			run_meth = getattr(crawler, "run")
			if asyncio.iscoroutinefunction(run_meth):
				await run_meth()
				return
		if hasattr(crawler, "main"):
			run_meth = getattr(crawler, "main")
			if asyncio.iscoroutinefunction(run_meth):
				await run_meth()
				return

	raise RuntimeError("Crawler module does not expose an async entrypoint we can call")


def run_processor_module(mod, input_dir: str, *, verbose: bool = True):
	"""Run the processor from the loaded module by instantiating
	PineScriptDocsProcessor(input_dir, output_dir) and calling process_all().
	"""
	if not hasattr(mod, "PineScriptDocsProcessor"):
		raise RuntimeError("Processor module does not define PineScriptDocsProcessor")

	if verbose:
		print(f"Running processor against: {input_dir}")

	Processor = getattr(mod, "PineScriptDocsProcessor")
	processor = Processor(input_dir, "processed")
	# process_all is synchronous in the provided file
	processor.process_all()


def main(argv: list[str] | None = None):
	argv = argv if argv is not None else sys.argv[1:]
	parser = argparse.ArgumentParser(description="Run scraper and processor")
	group = parser.add_mutually_exclusive_group()
	group.add_argument("--crawl-only", action="store_true", help="Only run the crawler")
	group.add_argument("--process-only", action="store_true", help="Only run the processor")
	parser.add_argument("--no-verbose", dest="verbose", action="store_false", help="Reduce output")
	args = parser.parse_args(argv)

	repo_dir = Path(__file__).resolve().parent
	path_scraper = str(repo_dir / "1_scrap_docs.py")
	path_processor = str(repo_dir / "2_process_docs.py")

	# Load modules using unique names so they don't conflict with imports
	scraper_mod = load_module_from_path("_pinescraper_1", path_scraper)
	processor_mod = load_module_from_path("_pinescraper_2", path_processor)

	# Decide what to run
	do_crawl = not args.process_only
	do_process = not args.crawl_only

	try:
		if do_crawl:
			# run the crawler's async main using asyncio.run
			asyncio.run(run_crawler_module(scraper_mod, verbose=args.verbose))
		else:
			if args.verbose:
				print("Skipping crawler step (per flags)")

		if do_process:
			# The crawler writes to pinescript_docs/unprocessed by default
			input_dir = os.path.join(str(repo_dir), "pinescript_docs", "unprocessed")
			if not os.path.isdir(input_dir):
				print(f"Warning: input directory not found: {input_dir}")
				print("Processor will still be invoked; it may decide to skip processing.")
			run_processor_module(processor_mod, input_dir, verbose=args.verbose)
		else:
			if args.verbose:
				print("Skipping processing step (per flags)")

	except Exception as e:
		print(f"Error during orchestration: {e}")
		raise


if __name__ == "__main__":
	main()

