import discord

# Tags Dictionaries

Designer_Tags = [
    discord.ForumTag(name="Accessory"),
    discord.ForumTag(name="Baby/Child"),
    discord.ForumTag(name="Book"),
    discord.ForumTag(name="Cardigan/Jacket"),
    discord.ForumTag(name="Dress/Skirt"),
    discord.ForumTag(name="Hat"),
    discord.ForumTag(name="Home"),
    discord.ForumTag(name="Man"),
    discord.ForumTag(name="Neckwear"),
    discord.ForumTag(name="Other"),
    discord.ForumTag(name="Socks"),
    discord.ForumTag(name="Sweater/Jumper"),
    discord.ForumTag(name="Top/Tank/Blouse"),
    discord.ForumTag(name="Toys"),
    discord.ForumTag(name="Vest/Slipover"),
    ]
Publisher_Tags = [
    
    discord.ForumTag(name="eBook"),
    discord.ForumTag(name="High Quality"),
    discord.ForumTag(name="Magazine"),
    discord.ForumTag(name="Single Pattern"),
    ]

def get_tags_for_category(category_name: str):
    if category_name in ["Publisher", "Yarn Houses and Brands"]:
        return Publisher_Tags
    else:
        return Designer_Tags