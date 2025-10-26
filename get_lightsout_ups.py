import logging

from loups import Loups

TEMPLATE = "data/template2.png"
TEMPLATE = "data/template_solid.png"
VIDEO = "data/emerald1.mp4"
VIDEO = "data/lbvibe2.mp4"
VIDEO = "data/lightsout_20251012_ruffrydaz12u.mp4"

logging.basicConfig(level=logging.INFO)
game = Loups(VIDEO, TEMPLATE).scan()
print(game.batters)
