FILTERS = set()
NSFW_FILTERS = {'loli', 'shota'}
HEADERS = {'User-Agent': "Shinobu (https://github.com/funketh/shinobu-bot)"}
NSFW_BOARDS = {"hentai", "rule34", "nekos_nsfw_classic", "nekos_nsfw_blowjob", "nekos_nsfw_boobs",
               "nekos_nsfw_neko", "nekos_nsfw_furry", "nekos_nsfw_pussy", "nekos_nsfw_feet",
               "nekos_nsfw_yuri", "nekos_nsfw_anal", "nekos_nsfw_solo", "nekos_nsfw_cum", "nekos_nsfw_spank",
               "nekos_nsfw_cunnilingus", "nekos_nsfw_bdsm", "nekos_nsfw_piercings",
               "nekos_nsfw_kitsune", "nekos_nsfw_holo", "nekos_nsfw_femdom", "r34"}
BOARDS = {'kon', 'yan', 'nekos_nsfw_blowjob', 'nekos_nsfw_yuri', 'nekos_sfw_waifu', 'nekos_nsfw_pussy',
          'nekos_nsfw_boobs', 'r34', 'rule34', 'nekos_nsfw_anal', 'nekos_nsfw_solo', 'nekos_nsfw_cunnilingus',
          'nekos_nsfw_cum', 'nekos_nsfw_furry', 'nekos_nsfw_neko', 'nekos_nsfw_femdom', 'nekos_nsfw_feet',
          'nekos_sfw_kitsune', 'hentai', 'nekos_sfw_holo', 'nekos_nsfw_kitsune', 'nekos_nsfw_holo',
          'nekos_nsfw_spank', 'nekos_sfw_smug', 'nekos_nsfw_piercings', 'dan', 'gel', 'nekos_nsfw_bdsm', 'safe',
          'nekos_nsfw_classic', 'nekos_sfw_neko'}


def tags_to_board(tag):
    # TODO
    return BOARDS.copy()
