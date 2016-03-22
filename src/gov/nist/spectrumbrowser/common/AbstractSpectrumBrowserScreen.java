package gov.nist.spectrumbrowser.common;

import gov.nist.spectrumbrowser.client.SpectrumBrowser;

import java.util.ArrayList;

import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.VerticalPanel;

public abstract class AbstractSpectrumBrowserScreen implements
		SpectrumBrowserScreen {

	private String endLabel;
	private ArrayList<SpectrumBrowserScreen> navigationScreens;
	private VerticalPanel verticalPanel;
	private AbstractSpectrumBrowser abstractSpectrumBrowser;


	public abstract void draw();

	@Override
	public String getLabel() {
		return endLabel + " >> ";
	}

	@Override
	public String getEndLabel() {
		return endLabel;
	}
	
	public static float round2(double val) {
		return (float) ((int) ((val + .005) * 100) / 100.0);
	}
	
	public static float round3(double val) {
		return (float) ((int) ((val + .0005) * 1000) / 1000.0);

	}
	
	public static float round(double val) {
		return (float) ((int) ((val + .05) * 10) / 10.0);
	}

	public void setNavigation(VerticalPanel verticalPanel,
			ArrayList<SpectrumBrowserScreen> navigation,
			AbstractSpectrumBrowser spectrumBrowser, String endLabel) {
		this.navigationScreens = navigation;
		this.verticalPanel = verticalPanel;
		this.abstractSpectrumBrowser = spectrumBrowser;
		this.endLabel = endLabel;
	}

	public ArrayList<SpectrumBrowserScreen> getNavigation() {
		return this.navigationScreens;
	}
	
	public void drawNavigation() {
	
		if (navigationScreens != null) {
			MenuBar menuBar = new MenuBar();
			verticalPanel.add(menuBar);
			for (int i = 0; i < navigationScreens.size() - 1; i++) {
				final SpectrumBrowserScreen thisScreen = navigationScreens.get(i);
				menuBar.addItem(
						new SafeHtmlBuilder().appendEscaped(
								navigationScreens.get(i).getLabel()).toSafeHtml(),
						new Scheduler.ScheduledCommand() {

							@Override
							public void execute() {
								thisScreen.draw();
							}
						});
			}

			menuBar.addItem(
					new SafeHtmlBuilder().appendEscaped(
							navigationScreens.get(navigationScreens.size() - 1)
									.getEndLabel()).toSafeHtml(),
					new Scheduler.ScheduledCommand() {

						@Override
						public void execute() {
							navigationScreens.get(navigationScreens.size() - 1)
									.draw();
						}
					});

			if (abstractSpectrumBrowser.isUserLoggedIn()) {
				menuBar.addItem(new SafeHtmlBuilder().appendEscaped("Log Off")
						.toSafeHtml(), new Scheduler.ScheduledCommand() {
					@Override
					public void execute() {
						abstractSpectrumBrowser.logoff();
					}
				});

			}

		}

	}
	
	public void navigateToPreviousScreen() {
		if (this.navigationScreens != null) {
			SpectrumBrowserScreen lastScreen = this.navigationScreens.get(this.navigationScreens.size() - 1);
			lastScreen.draw();
		}
	}
	
	protected String getAsString(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return jsonObject.get(keyName).isString().stringValue();
		} else {
			return "UNDEFINED";
		}
		
	}
	
	protected int getAsInt(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return (int)jsonObject.get(keyName).isNumber().doubleValue();
		} else {
			return 0;
		}
	}
	
	protected long getAsLong(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return (long)jsonObject.get(keyName).isNumber().doubleValue();
		} else {
			return 0;
		}
	}
	
	protected boolean getAsBoolean(JSONValue jsonValue, String keyName) {
		JSONObject jsonObject = jsonValue.isObject();
		if (jsonObject.containsKey(keyName)) {
			return jsonObject.get(keyName).isBoolean().booleanValue();
		} else {
			return false;
		}
	}

}
