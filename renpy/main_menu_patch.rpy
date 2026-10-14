init:
    if getattr(renpy.bootstrap, "tbmm_initialized", False):

        screen main_menu_mods:
            tag menu
            style_prefix "main_menu"

            use main_menu_old

            imagebutton:
                auto "TBModManager/assets/images/logo_%s.png"
                hover_sound "sounds/menu/menu-button-select-3.ogg"
                activate_sound "sounds/menu/language-sellect-1.ogg"
                xalign 0.95
                yalign 0.95
                action ShowMenu("mods", _transition=Fade(0.0, 0.0, 0.5))
                at mm_elements

init 1 python:
    if getattr(renpy.bootstrap, "tbmm_initialized", False):

        renpy.display.screen.screens[("main_menu_old", None)] = renpy.display.screen.screens[("main_menu", None)]
        renpy.display.screen.screens[("main_menu", None)] = renpy.display.screen.screens[("main_menu_mods", None)]
