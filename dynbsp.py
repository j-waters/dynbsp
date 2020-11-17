#!/usr/bin/env python
import logging

import click

from config import CONFIG
from helpers import clear_empty_desktops, new_misc_desktop, rename_all, \
 create_home, reorder, update_names, new_monitor_added, remove_old_monitors
from pybspc import *

logging.basicConfig(filename='dynbspwm.log',
					format='%(asctime)s | %(filename)s:%(lineno)d | %(funcName)s | %(levelname)s | %(message)s',
					level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())

sub = Subscriber()


@sub.event('node_add')
def node_added(wm: BSPWM, monitor: Monitor, desktop: Desktop, node: Node):
	app_config = CONFIG.match_node(node)
	if app_config is not None:
		target_desktop = app_config.desktop.find(wm, exclude_nodes={node})
		if target_desktop is None:
			target_desktop = app_config.desktop.create(wm.current_monitor)
		if desktop != target_desktop:
			node.to_desktop(target_desktop)
		app_config.desktop.update_name(target_desktop, wm)
	else:
		if CONFIG.match_home(desktop):
			new_misc_desktop(True, node, wm)
	reorder(get_wm())
	logging.info(f"Node added {node}, {desktop}")


@sub.event('node_remove')
def node_removed(wm: BSPWM, monitor: Monitor, desktop: Desktop, node: Node):
	if len(desktop.nodes) == 0:
		desktop.delete()


@sub.event('desktop_remove')
def desktop_removed(wm, monitor: Monitor, desktop: Desktop):
	update_names(wm)


@sub.event('monitor_add')
def monitor_add(wm, monitor: Monitor):
	new_monitor_added(monitor, wm)


@sub.event('node_transfer')
def node_transfer(wm, src_monitor: Monitor, src_desktop: Desktop, src_node: Node, dst_monitor: Monitor,
					dst_desktop: Desktop, dst_node: Node):
	clear_empty_desktops(src_monitor)


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
	if ctx.invoked_subcommand is None:
		start()


@cli.command()
def start():
	create_home()
	clear_empty_desktops(get_wm())
	rename_all()
	update_names()
	reorder()
	sub.listen()


@cli.command()
def multimonitor():
	remove_old_monitors()


@cli.command()
@click.option('--move', default=False, is_flag=True, help='move current node to desktop')
def new_desktop(move):
	new_misc_desktop(move)


if __name__ == '__main__':
	cli()
