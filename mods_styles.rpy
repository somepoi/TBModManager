init -999:

    if getattr(renpy.bootstrap, "tbmm_initialized", False):

        style mods_button is main_menu_button:
            background "interface/button.png"
            hover_background "TBModManager/assets/images/button_hover.png"
            xminimum 438
            yminimum 86

        style mods_button_text is main_menu_button_text:
            color "#000"
            hover_color "#fff"
            text_align 0.5
            size 38
        
        style mods_sort_button is main_menu_button
        style mods_sort_button_text is main_menu_button_text:
            size 48
            idle_color "#aaaaaa"
            hover_color "#ffffff"
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_main_container:
            area (100, 80, 1720, 920)
            background Solid("#000000cc")
            padding (20, 20)

        style mods_main_hbox:
            spacing 20

        style mods_left_panel:
            xsize 1100
            ysize 880
            background Solid("#00000099")
            
            padding (15, 15)

        style mods_right_panel:
            xsize 560
            ysize 880
            background Solid("#00000099")
            padding (15, 15)

        style mods_main_vbox:
            spacing 10

        style mods_header_hbox:
            spacing 20
            xfill True

        style mods_header_text:
            size 48
            color "#ffffff"
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_search_frame:
            xfill True
            background At(AlphaMask("#ffffff22", Frame("TBModManager/assets/images/mask.webp", Borders(30, 30, 30, 30))), Transform(alpha=0.65))
            padding (12, 8)
            xmaximum 1060

        style mods_search_hbox:
            spacing 12
            yalign 0.5

        style mods_search_input_hbox:
            spacing 0

        style mods_search_input:
            size 40
            color "#ffffff"
            yalign 0.5

        style mods_search_placeholder_text:
            size 40
            color "#666666"
            yalign 0.5
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_counter_text:
            size 32
            color "#aaaaaa"
            xalign 0.0
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_list_viewport:
            xfill True
            yfill True

        style mods_list_vbox:
            spacing 8

        style mods_list_item_button:
            xsize 1020
            ysize 100
            background Solid("#ffffff11")
            hover_background Solid("#ffffff33")
            hover_sound None

        style mods_list_item_hbox:
            spacing 15
            xalign 0.0
            yalign 0.5

        style mods_list_item_avatar:
            xsize 80
            ysize 80

        style mods_list_item_vbox:
            spacing 5
            yalign 0.5
            xmaximum 900

        style mods_list_item_name_text:
            size 40
            color "#ffffff"
            font "font/russia.ttf"
            xmaximum 900
            xalign 0.0

        style mods_list_item_author_text:
            size 28
            color "#aaaaaa"
            xmaximum 900
            xalign 0.0

        style mods_empty_frame:
            xsize 1100
            ysize 540
            background None
            padding (15, 15)

        style mods_empty_vbox:
            xalign 0.5
            yalign 0.5
            spacing 20

        style mods_empty_title_text:
            size 62
            color "#666666"
            xalign 0.5
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_empty_subtitle_text:
            size 50
            color "#555555"
            xalign 0.5
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_info_header_text:
            size 48
            color "#ffffff"
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_info_avatar_frame:
            background None
            xalign 0.5
            padding (10, 10)
            xmaximum 256
            ymaximum 256

        style mods_info_name_text:
            color "#ffffff"
            font "font/russia.ttf"
            xalign 0.5
            text_align 0.5
            xmaximum 500

        style mods_info_author_text:
            size 32
            color "#aaaaaa"
            xalign 0.5
            text_align 0.5
            xmaximum 500

        style mods_info_desc_frame:
            xfill True
            yfill True
            background Solid("#ffffff11")
            padding (15, 15)
            xmaximum 525
            ymaximum 500

        style mods_info_desc_viewport:
            xfill True
            yfill True

        style mods_info_desc_text:
            size 18
            font "font/GenEiAntiqueNv5-M.ttf"
            color "#dddddd"
            text_align 0.0
            xalign 0.0
            xmaximum 500

        style mods_placeholder_vbox:
            xalign 0.5
            yalign 0.5
            spacing 30

        style mods_placeholder_icon_text:
            size 240
            color "#333333"
            xalign 0.5
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_placeholder_message_text:
            size 50
            color "#666666"
            text_align 0.5
            xalign 0.5
            font ("font/russia.ttf" if preferences.language not in ("japan", "chinese") else other_font_interface)

        style mods_info_vbox:
            spacing 20
            xfill True

        style mods_outer_vbox:
            spacing 78