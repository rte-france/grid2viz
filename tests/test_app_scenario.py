import configparser
import os
import pathlib
import unittest
import time
import dash_html_components as html

# We need to make this below so that the manager.py finds the config.ini
os.environ["GRID2VIZ_ROOT"] = os.path.join(
    pathlib.Path(__file__).parent.absolute(), "data"
)

config_file_path = os.path.join(os.environ["GRID2VIZ_ROOT"], "config.ini")

def test_navigation_scenario_1(dash_duo):

    start_time=time.time()

    parser = configparser.ConfigParser()
    parser.read(config_file_path)

    agents_path = parser.get("DEFAULT", "agents_dir")
    cache_dir = os.path.join(agents_path, "_cache")
    if not os.path.isdir(cache_dir):
        from tests.test_make_cache import TestMakeCache
        test_make_cache = TestMakeCache()
        test_make_cache.setUp()
        test_make_cache.test_make_cache()
    agent_name = "do-nothing-baseline"
    scenario_name = "000"
    env_path = parser.get("DEFAULT", "env_dir")
    print('starting')
    from grid2viz.app_heroku import app
    dash_duo.start_server(app)
    dash_duo.driver.maximize_window()#so that floating parts on nav bar don't overlap too much with tab titles when in agent study
    print("elapsed time is: "+str(time.time() -start_time))

    #####
    #loading front page scenario selection
    #dash_duo.wait_for_page("http://localhost:8050/")
    dash_duo.wait_for_text_to_equal("#scen_lbl", "")#, timeout=15)
    #assert False
    print("elapsed time is: " + str(time.time() - start_time))
    dash_duo.wait_for_element("#scen_lbl",timeout=15)
    dash_duo.wait_for_text_to_equal("#scen_lbl", "", timeout=15)
    dash_duo.wait_for_text_to_equal("#select_ref_agent", "Ref Agent", timeout=5)
    dash_duo.wait_for_text_to_equal("#select_study_agent", "Study Agent", timeout=5)
    #dash_duo.wait_for_text_to_equal("#scen_lbl", "000", timeout=200)

    dash_duo.wait_for_element("#collapse-button", timeout=15)
    #dash_duo.multiple_click("#nav_agent_study", 1)
    #dash_duo.wait_for_element("#scenarios_filter", timeout=15)
    #assert (not dash_duo.wait_for_element_by_id("scenarios_filter").is_displayed())

    print(app._layout)
    #dash_duo.wait_for_page("http://localhost:8050/episodes", timeout=20)

    dash_duo.wait_for_element("#card_000",timeout=15)
    #dash_duo.wait_for_element_by_id("000",timeout=15)

    dash_duo.wait_for_element("#card_001", timeout=15)
    #dash_duo.wait_for_element_by_id("001",timeout=15)

    assert (not dash_duo.wait_for_element_by_id("select_ref_agent").is_enabled())
    assert (not dash_duo.wait_for_element_by_id("select_study_agent").is_enabled())

    ####@
    #test collapse button and open to dispaly heatmap and scenario filtering
    #ideally flter only one scenario and test interaction. But don't seem possible, scenario_filter is said to be non interactable
    #assert (not dash_duo.wait_for_element_by_id("scenarios_filter").is_displayed())
    #assert (not dash_duo.wait_for_element_by_id("heatmap attention").is_displayed())
    #assert (not dash_duo.wait_for_element_by_id("heatmap survival").is_displayed())
#
    #dash_duo.multiple_click("#collapse-button", 1)
    #dash_duo.wait_for_text_to_equal("#scenarios_filter",'000\n001',timeout=15)
    ##dash_duo.wait_for_element_by_id("scenarios_filter").click().send_keys(Keys.DELETE)
    ##dash_duo.clear_input("#scenarios_filter")
    #assert (dash_duo.wait_for_element_by_id("scenarios_filter").is_displayed())
    #assert (dash_duo.wait_for_element_by_id("heatmap attention").is_displayed())
    #assert (dash_duo.wait_for_element_by_id("heatmap survival").is_displayed())


    ####
    #switch to page overview scenario
    #dash_duo.wait_for_element_by_id("001").click()
    y=0.8
    while (dash_duo.wait_for_element("#scen_lbl", timeout=15).text == ""):
        dash_duo.click_at_coord_fractions("#card_001", 0.5, y)
        y+=0.05
    #if(dash_duo.wait_for_element("#scen_lbl",timeout=15).text==""):
    #    while (dash_duo.wait_for_element("#scen_lbl",timeout=15).text==""):
    #        print("waiting for text scenario to update after choosing scenario")
    #print(dash_duo.wait_for_element("#scen_lbl",timeout=15).text)
    #dash_duo.wait_for_text_to_equal("#scen_lbl", "001", timeout=20)
    #dash_duo.wait_for_text_to_equal("#select_ref_agent", "do-nothing-baseline", timeout=20)
    #dash_duo.wait_for_page("http://localhost:8050/overview/") #this loads the page rather than just checking the url



    dash_duo.wait_for_text_to_equal("#select_study_agent", "greedy-baseline", timeout=20)
    dash_duo.wait_for_text_to_equal("#select_ref_agent", "do-nothing-baseline", timeout=20)
    assert (dash_duo.wait_for_element_by_id("select_ref_agent").is_enabled())
    assert(not dash_duo.wait_for_element_by_id("select_study_agent").is_enabled())

    #######
    #switch to page agent overview and click on reward timeserie graph to select a timestep to study
    dash_duo.multiple_click("#nav_agent_over", 1)
    assert ( dash_duo.wait_for_element_by_id("select_study_agent").is_enabled())
    dash_duo.wait_for_element_by_id("rewards_timeserie",timeout=10)
    #dash_duo.wait_for_page("http://localhost:8050/macro")


    dash_duo.wait_for_element_by_id("rewards_timeserie")#.click()
    while(dash_duo.wait_for_element_by_id("timeseries_table",timeout=10).text=='Timestamps'):
        dash_duo.click_at_coord_fractions("#rewards_timeserie", 0.2, 0.2)
    dash_duo.wait_for_text_to_equal("#timeseries_table",'Timestamps\n× 2019-01-07 02:45',timeout=20)

    assert (not dash_duo.wait_for_element_by_id("user_timestamps").is_displayed())

    #######
    # switch to page agent study and check timestep
    dash_duo.multiple_click("#nav_agent_study", 1)
    assert (dash_duo.wait_for_element_by_id("user_timestamps").is_displayed())
    dash_duo.wait_for_text_to_equal("#user_timestamps", '2019-01-07 02:45\n×', timeout=20)
    txt_slider = dash_duo.wait_for_element_by_css_selector("#slider").text
    while (len(txt_slider)==0):
        txt_slider = dash_duo.wait_for_element_by_css_selector("#slider").text
    slider_hours=txt_slider.split('\n')
    print(slider_hours)
    assert(len(slider_hours)==20)#asserting number of timesteps in slider
    assert(slider_hours[10]=='02:45:00')#checking that it is centered on the user_timestamp

    dash_duo.multiple_click("#enlarge_left",1)
    while (dash_duo.wait_for_element_by_css_selector("#slider").text == txt_slider):
        print('waiting slider text to be updated')
    txt_slider = dash_duo.wait_for_element_by_css_selector("#slider").text
    slider_hours = txt_slider.split('\n')
    assert (slider_hours[10] == '02:20:00')#should have moved by 5 timesteps earlier

    #######
    #get back to agent_overview page and check that timestamps always store the previously selected one
    dash_duo.multiple_click("#nav_agent_over", 1)
    dash_duo.wait_for_text_to_equal("#timeseries_table", 'Timestamps\n× 2019-01-07 02:45', timeout=20)

    ######
    #return to initial scenario selection page and end
    #dash_duo.wait_for_text_to_equal("#scen_lbl", "000", timeout=200)
    dash_duo.multiple_click("#nav_scen_select", 1)
    dash_duo.wait_for_element("#card_001", timeout=15)
    #dash_duo.multiple_click("#nav_scen_over", 1)
    print('finished')