package gov.nist.spectrumbrowser.admin;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.TextBox;

import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserWidget;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;
import gov.nist.spectrumbrowser.common.SpectrumBrowserScreen;


public class ESAgents extends AbstractSpectrumBrowserWidget implements
SpectrumBrowserCallback<String>, SpectrumBrowserScreen {
	public static final String LABEL=null;
	public static final String END_LABEL = "Sensing Agents";
	private Admin admin;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private JSONArray esAgents;
	private Grid grid;
	private boolean redraw;

	private class DeleteClickHandler implements ClickHandler {
		String agentName;

		public DeleteClickHandler( String agentName) {
			this.agentName = agentName;
		}
		
		@Override
		public void onClick(ClickEvent event) {
			redraw = true;
			try {
				Admin.getAdminService().deleteESAgent(agentName,ESAgents.this);
			} catch ( Throwable th) {
				logger.log(Level.SEVERE, "Error communicating with server",th);
				Window.alert("error communicating with server");
				admin.logoff();
			}
		}}

	public ESAgents(Admin admin) {
		try {
			this.admin = admin;
			Admin.getAdminService().getESAgents(this);
		} catch (Throwable th) {
			Window.alert("Problem contacting server");
			logger.log(Level.SEVERE,"Problem contacting server", th);
			admin.logoff();
		}
	}

	@Override
	public void draw() {
		verticalPanel.clear();
		HTML html = new HTML("<h2>Agent identities that can steer streaming and trigger I/Q capture</h2>");
		verticalPanel.add(html);
		int rows = esAgents.size();
		grid = new Grid(rows+1,3);
		grid.setText(0, 0, "Agent Name");
		grid.setText(0, 1, "Agent Key");
		grid.setText(0, 2, "Delete");
		verticalPanel.add(html);
		grid.setBorderWidth(2);
		grid.setCellPadding(2);
		grid.setCellPadding(2);
		
		for (int i = 1; i < rows+1; i++) {
			JSONObject agents = esAgents.get(i-1).isObject();
			grid.setText(i, 0, agents.get("agentName").isString().stringValue());
			grid.setText(i, 1, agents.get("key").isString().stringValue());
			Button delete = new Button("Delete");
			grid.setWidget(i, 2, delete);
			delete.addClickHandler( new DeleteClickHandler(agents.get("agentName").isString().stringValue()));
		}
		
		for (int i = 0; i < grid.getColumnCount(); i++) {
			grid.getCellFormatter().setStyleName(0, i, "textLabelStyle");
		}
		
		
		for (int i = 0; i < grid.getRowCount(); i++) {
			for (int j = 0; j < grid.getColumnCount(); j++) {
				grid.getCellFormatter().setHorizontalAlignment(i, j,
						HasHorizontalAlignment.ALIGN_CENTER);
				grid.getCellFormatter().setVerticalAlignment(i, j,
						HasVerticalAlignment.ALIGN_MIDDLE);
			}
		}
		verticalPanel.add(grid);
		HorizontalPanel buttonPanel = new HorizontalPanel();
		Button addPeerButton = new Button ("Add");
		addPeerButton.addClickHandler(new ClickHandler() {
			@Override
			public void onClick(ClickEvent event) {
				redraw = true;
				new AddEsAgent(admin, ESAgents.this,verticalPanel).draw();
			}});
		buttonPanel.add(addPeerButton);
		Button logoffButton = new Button("Log Off");
		
		logoffButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				admin.logoff();
			}});
		buttonPanel.add(logoffButton);
		verticalPanel.add(buttonPanel);
	}

	@Override
	public String getLabel() {
		return LABEL;
	}

	@Override
	public String getEndLabel() {
		return END_LABEL;
	}

	@Override
	public void onSuccess(String result) {
		logger.log(Level.FINER, " ESAgents:onSuccess " + result);
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			esAgents = jsonValue.isObject().get("esAgents").isArray();	
			if (redraw) {
				this.draw();
			}
		} catch (Throwable th) {
			Window.alert("Error parsing returned JSON");
			logger.log(Level.SEVERE, "Problem parsing JSON", th);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub
		
	}

}
