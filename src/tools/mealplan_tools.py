import logging
import traceback
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from mealie import MealieFetcher
from models.mealplan import MealPlanEntry

logger = logging.getLogger("mealie-mcp")


def register_mealplan_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    """Register all mealplan-related tools with the MCP server."""

    @mcp.tool()
    def get_all_mealplans(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get all meal plans for the current household with pagination.

        Args:
            start_date: Start date for filtering meal plans (ISO format YYYY-MM-DD)
            end_date: End date for filtering meal plans (ISO format YYYY-MM-DD)
            page: Page number to retrieve
            per_page: Number of items per page

        Returns:
            Dict[str, Any]: JSON response containing mealplan items and pagination information
        """
        try:
            logger.info(
                {
                    "message": "Fetching mealplans",
                    "start_date": start_date,
                    "end_date": end_date,
                    "page": page,
                    "per_page": per_page,
                }
            )
            return mealie.get_mealplans(
                start_date=start_date,
                end_date=end_date,
                page=page,
                per_page=per_page,
            )
        except Exception as e:
            error_msg = f"Error fetching mealplans: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def create_mealplan(
        date: str,
        recipe_id: Optional[str] = None,
        title: Optional[str] = None,
        entry_type: str = "breakfast",
    ) -> Dict[str, Any]:
        """Create a new meal plan entry.

        Args:
            date: Date for the mealplan in ISO format (YYYY-MM-DD)
            recipe_id: UUID of the recipe to add to the mealplan (optional)
            title: Title for the mealplan entry if not using a recipe (optional)
            entry_type: Type of mealplan entry (breakfast, lunch, dinner, side)

        Returns:
            Dict[str, Any]: JSON response containing the created mealplan entry
        """
        try:
            logger.info(
                {
                    "message": "Creating mealplan entry",
                    "date": date,
                    "recipe_id": recipe_id,
                    "title": title,
                    "entry_type": entry_type,
                }
            )
            return mealie.create_mealplan(
                date=date,
                recipe_id=recipe_id,
                title=title,
                entry_type=entry_type,
            )
        except Exception as e:
            error_msg = f"Error creating mealplan entry: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def create_mealplan_concise(
        date: str,
        recipe_slug: Optional[str] = None,
        recipe_id: Optional[str] = None,
        title: Optional[str] = None,
        entry_type: str = "breakfast",
    ) -> Dict[str, Any]:
        """Create a new meal plan entry. Returns a concise response with only essential fields
        instead of the full recipe object.

        Prefer using recipe_slug over recipe_id — slugs are human-readable strings like
        "zesty-chicken-meatballs" from the get_recipes_concise results.

        Args:
            date: Date for the mealplan in ISO format (YYYY-MM-DD)
            recipe_slug: Slug of the recipe (e.g. "zesty-chicken-meatballs"). Preferred over recipe_id.
            recipe_id: UUID of the recipe (optional, use recipe_slug instead when possible)
            title: Title for the mealplan entry if not using a recipe (optional)
            entry_type: Type of mealplan entry (breakfast, lunch, dinner, side)

        Returns:
            Dict[str, Any]: Concise mealplan entry with id, date, entryType, recipe_name, and recipe_slug.
        """
        try:
            # Resolve slug to ID if needed
            if recipe_slug and not recipe_id:
                recipe_data = mealie.get_recipe(recipe_slug)
                recipe_id = recipe_data.get("id")

            logger.info(
                {
                    "message": "Creating mealplan entry (concise)",
                    "date": date,
                    "recipe_id": recipe_id,
                    "title": title,
                    "entry_type": entry_type,
                }
            )
            result = mealie.create_mealplan(
                date=date,
                recipe_id=recipe_id,
                title=title,
                entry_type=entry_type,
            )
            concise = {
                "id": result.get("id"),
                "date": result.get("date"),
                "entryType": result.get("entryType"),
                "title": result.get("title"),
            }
            recipe = result.get("recipe")
            if recipe:
                concise["recipe_name"] = recipe.get("name")
                concise["recipe_slug"] = recipe.get("slug")
            return concise
        except Exception as e:
            error_msg = f"Error creating mealplan entry (concise): {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def get_all_mealplans_concise(
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get all meal plans with only essential fields (no full recipe objects).

        Args:
            start_date: Start date for filtering meal plans (ISO format YYYY-MM-DD)
            end_date: End date for filtering meal plans (ISO format YYYY-MM-DD)
            page: Page number to retrieve
            per_page: Number of items per page

        Returns:
            Dict[str, Any]: Mealplan entries with id, date, entryType, title, recipe_name, and recipe_slug.
        """
        try:
            logger.info(
                {
                    "message": "Fetching mealplans (concise)",
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )
            result = mealie.get_mealplans(
                start_date=start_date,
                end_date=end_date,
                page=page,
                per_page=per_page,
            )
            if "items" in result:
                result["items"] = [
                    {
                        "id": item.get("id"),
                        "date": item.get("date"),
                        "entryType": item.get("entryType"),
                        "title": item.get("title"),
                        "recipe_name": item.get("recipe", {}).get("name") if item.get("recipe") else None,
                        "recipe_slug": item.get("recipe", {}).get("slug") if item.get("recipe") else None,
                    }
                    for item in result["items"]
                ]
            return result
        except Exception as e:
            error_msg = f"Error fetching mealplans (concise): {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def get_todays_mealplan_concise() -> List[Dict[str, Any]]:
        """Get today's mealplan entries with only essential fields.

        Returns:
            List[Dict[str, Any]]: Today's mealplan entries with id, date, entryType, title,
                recipe_name, and recipe_slug.
        """
        try:
            logger.info({"message": "Fetching today's mealplan (concise)"})
            result = mealie.get_todays_mealplan()
            return [
                {
                    "id": item.get("id"),
                    "date": item.get("date"),
                    "entryType": item.get("entryType"),
                    "title": item.get("title"),
                    "recipe_name": item.get("recipe", {}).get("name") if item.get("recipe") else None,
                    "recipe_slug": item.get("recipe", {}).get("slug") if item.get("recipe") else None,
                }
                for item in result
            ]
        except Exception as e:
            error_msg = f"Error fetching today's mealplan (concise): {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def create_mealplan_bulk(
        entries: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create multiple meal plan entries in bulk.

        Args:
            entries: List of mealplan entries, each containing:
                - date (str): Date in ISO format (YYYY-MM-DD)
                - recipe_id (str, optional): UUID of the recipe
                - title (str, optional): Title for the entry
                - entry_type (str, optional): Type of entry (breakfast, lunch, dinner, side)

        Returns:
            Dict[str, Any]: JSON response with success message
        """
        try:
            logger.info(
                {
                    "message": "Creating bulk mealplan entries",
                    "entries_count": len(entries),
                }
            )
            for entry in entries:
                entry_obj = MealPlanEntry.model_validate(entry)
                mealie.create_mealplan(**entry_obj.model_dump())
            return {"message": f"Successfully created {len(entries)} mealplan entries"}
        except Exception as e:
            error_msg = f"Error creating bulk mealplan entries: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def get_todays_mealplan() -> List[Dict[str, Any]]:
        """Get the mealplan entries for today.

        Returns:
            List[Dict[str, Any]]: List of today's mealplan entries
        """
        try:
            logger.info({"message": "Fetching today's mealplan"})
            return mealie.get_todays_mealplan()
        except Exception as e:
            error_msg = f"Error fetching today's mealplan: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)
