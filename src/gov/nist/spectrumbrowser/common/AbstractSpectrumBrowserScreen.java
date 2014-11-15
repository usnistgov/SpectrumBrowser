package gov.nist.spectrumbrowser.common;

import java.util.ArrayList;

import com.google.gwt.core.client.Scheduler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
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

	public void setNavigation(VerticalPanel verticalPanel,
			ArrayList<SpectrumBrowserScreen> navigation,
			AbstractSpectrumBrowser spectrumBrowser, String endLabel) {
		this.navigationScreens = navigation;
		this.verticalPanel = verticalPanel;
		this.abstractSpectrumBrowser = spectrumBrowser;
		this.endLabel = endLabel;
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

}
