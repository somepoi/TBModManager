# TODO: парс аватарки из стима по номеру мода
# TODO: парс имени автора(ов) из стима по номеру мода
# TODO: парс описания из стима по номеру мода
# TODO: парс последней даты обновления

init -999:
    if getattr(renpy.bootstrap, "tbmm_initialized", False):

        screen mod_empty_state(title, subtitle):
            style_prefix "mods_empty"

            frame:
                vbox:
                    text _(title):
                        style "mods_empty_title_text"

                    text _(subtitle):
                        style "mods_empty_subtitle_text"

        screen mod_info_placeholder(message):
            style_prefix "mods_placeholder"

            vbox:
                text "?":
                    style "mods_placeholder_icon_text"

                text _(message):
                    style "mods_placeholder_message_text"

        screen mods:
            modal True
            tag menu

            add gui.main_menu_background
            add "menu002_1"
            add "menu002_2"
            add "chastichka_2"
            add "menu001_1"
            add "menu001_2"
            add "chastichka_1_1"
            add "chastichka_1_2"
            add "bg_black" at mm_bg_diss_1to0

            vbox:
                style "mods_outer_vbox"

                frame:
                    style "mods_main_container"

                    hbox:
                        style "mods_main_hbox"

                        frame:
                            style "mods_left_panel"

                            vbox:
                                style "mods_main_vbox"

                                hbox:
                                    style "mods_header_hbox"

                                    text _("МЕНЕДЖЕР МОДОВ"):
                                        style "mods_header_text"

                                    null width 20

                                    if tbmm_store.mods:
                                        if tbmm_store.mod_sort_reverse:
                                            $ sort_text = _("Сортировка: Я-А")
                                        else:
                                            $ sort_text = _("Сортировка: А-Я")

                                        textbutton sort_text:
                                            style "mods_sort_button"
                                            action Function(tbmm_store.toggle_mod_sort)
                                            align (1.0, 0.5)

                                if tbmm_store.mods:
                                    null height 15

                                    frame:
                                        style "mods_search_frame"

                                        hbox:
                                            style "mods_search_hbox"

                                            add "TBModManager/assets/images/search_small.png" align(0.5, 0.5)

                                            hbox style "mods_search_input_hbox":
                                                input:
                                                    style "mods_search_input"
                                                    value FieldInputValue(tbmm_store, "mod_search_query")
                                                    length 100
                                                    allow None
                                                    default ""
                                                    copypaste True

                                                if not tbmm_store.mod_search_query:
                                                    text _("Поиск по названию, описанию или автору..."):
                                                        style "mods_search_placeholder_text"

                                    null height 10

                                    $ filtered_mods = tbmm_store.get_filtered_mods()
                                    $ filtered_count = len(filtered_mods)

                                    if tbmm_store.mod_search_query:
                                        text _("Найдено: [filtered_count]"):
                                            style "mods_counter_text"

                                    null height 5

                                    if filtered_mods:
                                        viewport:
                                            style "mods_list_viewport"
                                            id "mods_viewport"
                                            draggable True
                                            mousewheel True
                                            scrollbars ("vertical" if filtered_count > 6 else None)

                                            vbox:
                                                style "mods_list_vbox"

                                                for label, mod in filtered_mods:
                                                    button:
                                                        style "mods_list_item_button"
                                                        hovered [SetField(tbmm_store, "selected_mod", mod)]
                                                        action Start(label)

                                                        hbox:
                                                            style "mods_list_item_hbox"

                                                            if mod.avatar:
                                                                add mod.avatar:
                                                                    xysize(80, 80)
                                                                    align(0.5, 0.5)
                                                            else:
                                                                add "TBModManager/assets/images/avatar_placeholder.png":
                                                                    xysize(80, 80)
                                                                    align(0.5, 0.5)

                                                            vbox:
                                                                style "mods_list_item_vbox"

                                                                text mod.get_truncated_name():
                                                                    style "mods_list_item_name_text"

                                                                if mod.authors:
                                                                    text mod.get_authors():
                                                                        style "mods_list_item_author_text"
                                    else:
                                        use mod_empty_state("Ничего не найдено", "Попробуйте изменить поисковый запрос")
                                else:
                                    null height 100
                                    use mod_empty_state("Моды не найдены", "Установите моды в папку игры")

                        frame:
                            style "mods_right_panel"

                            if tbmm_store.selected_mod:
                                vbox:
                                    style "mods_info_vbox"

                                    text _("ИНФОРМАЦИЯ О МОДЕ"):
                                        style "mods_info_header_text"

                                    null height 10

                                    if tbmm_store.selected_mod.avatar:
                                        frame:
                                            style "mods_info_avatar_frame"

                                            add tbmm_store.selected_mod.avatar:
                                                fit "contain"
                                                xalign 0.5
                                                yalign 0.5
                                    else:
                                        add "TBModManager/assets/images/avatar_placeholder.png" xsize 256 ysize 256 xalign 0.5

                                    null height 20

                                    text tbmm_store.selected_mod.name:
                                        style "mods_info_name_text"
                                        size tbmm_store.selected_mod.get_adaptive_name_size()

                                    if tbmm_store.selected_mod.authors:
                                        text tbmm_store.selected_mod.get_authors():
                                            style "mods_info_author_text"

                                    python:
                                        import math
                                        desc_text = tbmm_store.selected_mod.description
                                        chars_per_line = 50
                                        estimated_lines = math.ceil(len(desc_text) / chars_per_line)
                                        line_height = 24
                                        estimated_height = estimated_lines * line_height
                                        needs_scrollbar = estimated_height > 220

                                    frame:
                                        style "mods_info_desc_frame"

                                        viewport:
                                            style "mods_info_desc_viewport"
                                            id "description_viewport"
                                            draggable True
                                            mousewheel True
                                            scrollbars ("vertical" if needs_scrollbar else None)

                                            text tbmm_store.selected_mod.description:
                                                style "mods_info_desc_text"
                            else:
                                if tbmm_store.mods:
                                    use mod_info_placeholder("Выберите мод из списка\nчтобы увидеть информацию")
                                else:
                                    use mod_info_placeholder("Установите моды\nчтобы увидеть информацию")

                textbutton _("Назад"):
                    style "mods_button"
                    xalign 0.5
                    keysym "game_menu"
                    action [SetField(tbmm_store, "mod_search_query", ""), SetField(tbmm_store, "selected_mod", ""), Return()]
