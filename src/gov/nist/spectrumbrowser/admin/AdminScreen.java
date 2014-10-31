package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Command;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.TextBox;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.google.gwt.user.client.ui.Button;

/**
 * Sample admin screen.
 * @author local
 *
 *Note: this is a sample admin screen class. It is structured in the same
 *way as the other screens (i.e. it implements SpectrumBrowserCallback). 
 *Right now it does nothing useful.
 */
class AdminScreen implements SpectrumBrowserCallback<String> {
	
	private VerticalPanel verticalPanel;
	private Admin adminEntryPoint;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	
	public AdminScreen(VerticalPanel verticalPanel, Admin adminEntryPoint) {
		logger.finer("AdminScreen");
		this.verticalPanel = verticalPanel;
		this.adminEntryPoint = adminEntryPoint;
	}

	public void draw() {
		
		verticalPanel.clear();
		HTML html = new HTML("<h1>First Admin Screen</h1> ", true);
		verticalPanel.add(html);
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();
		menuBar.addItem(
				safeHtml.appendEscaped(Admin.LOGOFF_LABEL)
						.toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						adminEntryPoint.logoff();

					}
				});

		menuBar.addItem("AdminScreen2", new Command(){
		      @Override
		      public void execute() {
		    	  new AdminScreen2(verticalPanel, AdminScreen.this.spectrumBrowser).draw();
		      }
		});
		verticalPanel.add(menuBar);
		TextBox textBox = new TextBox();
		textBox.setText("Admin Screen1.");
		verticalPanel.add(textBox);
		
	}

	@Override
	public void onSuccess(String result) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub
		
	}

}
